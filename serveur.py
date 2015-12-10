# -*- coding: utf-8 -*

#from Tkinter import*
import time
import os
import re
from socket import*
from threading import*



class Board :

	def __init__ (self, socket_1, socket_2) :

		self.height = 10
		self.width = 10
		self.grid = [[-1 for i in xrange(0,self.height,1)] for j in xrange(0,self.width,1)]

		self.init_board() 				# putting all pieces at their starting places


		# variables holding the state of the game
		self.sockets = {1:socket_1,2:socket_2}
		self.player = 2 				# whose turn it is to play
		self.highlight = []				# currently selected piece (coordinates on the board)
		self.moves = [] 				# possible moves for currently selected piece
		self.takeovers = []				# possible moves (for currently selected piece) involving the takeover of another piece
		self.play_again = False 		# does the player plays again ? (after a takeover)
		self.player_end_turn = False

		self.queens = [] 				# contains coordinates of all queens on the board (as they follow special rules)



		# to check possible huffs
		self.takeover_done = False
		self.last_moved = []
		self.huff_done = False
		self.possible_huff = []
		self.end = False



	def __repr__ (self) :

		string = ["----------------------------------------------------------------------------------------------------------------------------------------------------------"]
		string.append("\n")
		for i in xrange(0,len(self.grid),1) :
			string.append("\t".join([str(j) for j in self.grid[i]]))
			string.append("\n")
		string.append("----------------------------------------------------------------------------------------------------------------------------------------------------------")
		return "".join(string)


	# putting all pieces at their starting places
	def init_board (self) :

		for i in xrange (0,self.height,2) :
			for j in [0,2,6,8] :
				self.grid[i][j] = 1 + j/5
			self.grid[i][4] = 0

		for i in xrange (1,self.height,2) :
			for j in [1,3,7,9] :
				self.grid[i][j] = 1 + j/5
			self.grid[i][5] = 0

		#print self




	def left_click (self, x, y):
		# there are 2 possibilities : whether the player wants to select a piece or to move it

		if self.highlight == [] :					# if no piece is already selected (selecting a piece to move or huffing an opponent's one)
			self.select(x,y) 						# we call the "select" method in the game engine
														
		else :											# else the player wants to move a piece
			self.move(x,y)							# we call the "move" method

		# updating the drawing of the grid
		# everything done below :)

		send_sthg(self.sockets[1],["method","self.draw_grid_1(grid,queens)","grid",self.grid,"queens",self.queens])
		send_sthg(self.sockets[2],["method","self.draw_grid_2(grid,queens)","grid",self.grid,"queens",self.queens])
		#send draw_grid_1, grid, queens 	JOUEUR 1
		#send draw_grid_2, grid, queens		JOUEUR 2
		send_sthg(self.sockets[1],["method","self.draw_cemetery(grid,queens)","grid",self.grid,"queens",self.queens])
		send_sthg(self.sockets[2],["method","self.draw_cemetery(grid,queens)","grid",self.grid,"queens",self.queens])
		#send draw_cemetery, grid, queens	2 JOUEURS

		if not self.player_end_turn and self.highlight != []:
			send_sthg(self.sockets[self.player],["method","self.highlight_piece_1(coords)","coords",self.highlight])
			#send highlight_piece_1, highlight 	JOUEUR COURANT (self.player)
			send_sthg(self.sockets[self.player],["method","self.play()"])
			#send loop 							JOUEUR COURANT (self.player)

		elif self.player_end_turn :
			self.player = 3-self.player


		##########
		# if player == 1 :
		# 	self.draw_grid_1(self.game.grid,self.game.queens) 

		# else :
		# 	self.draw_grid_2(self.game.grid,self.game.queens) #SEND tell the client to draw the game

		# self.draw_cemetery(self.game.grid,self.game.queens) #SEND tell the client to draw the game


		# and highlighting the currently selected piece
		# if self.game.highlight != [] :

		# 	if self.game.player == 1 :
		# 		self.highlight_piece_1(self.game.highlight)
		# 	else :
		# 		self.highlight_piece_2(self.game.highlight)

		#self.check_end()
		##########



	# if no piece is currently selected, we assume the player wants to pick one :
	def select (self, x, y) :

		if self.grid[x][y] > 0 :

			self.possibilities(x,y)
	
			#print self.moves, self.takeovers 
			# if an action (move or takeover) is possible with the current selected piece :
			if self.moves != [] or self.takeovers != [] or [x,y] == self.possible_huff :

				# if the player has selected an opponent's piece (to huff it), and if no huff has already been done by this player
				if self.grid[x][y] != self.player and self.huff_done == False :

					self.check_huff(x,y)

				else :

					self.highlight = [x,y]
 



	# now the player wants to move the selected piece to the clicked square
	def move (self, x, y) :


		# if it is a standard move, for the first action of the player
		if [x,y] in self.moves and self.play_again == False :

			self.possible_huff = []

			self.takeover_done = False

			self.move_on_grid(x,y)

			if self.takeovers != [] :    # if this piece could have overtake an opponent's one, it is eligible to be huffed
				self.possible_huff = [x,y]
				#print self.possible_huff

			# end of player's turn
			self.end_turn()


		# if it is a takeover
		elif [x,y] in self.takeovers :

			self.possible_huff = []

			self.takeover_done = True

			self.move_on_grid(x,y)

			# we need to delete the piece that has been taken, that's easy to do if a piece has done the takeover
			if [x,y] not in self.queens :

				temp = (self.highlight[0] - x)/2
				temp2 = (self.highlight[1] - y)/2
				self.grid[x+temp][y+temp2] = 0
				if [x+temp,y+temp2] in self.queens :
					self.queens.remove([x+temp,y+temp2])
					#print self.queens

			# but trickier if a queen has been played (we don't know where the piece was)
			else :
				self.queen_takeover(x,y)

			self.takeovers = []

			self.select(x,y)						# can this player play again ? (by taking another opponent's piece)				

			if self.takeovers == [] :

				self.end_turn()

			else :

				self.play_again = True		
				# if yes, we keep the currently selected piece highlighted (so the player cannot cowardly play another one), and memorize the next possible takeover(s)
				self.moves = []


		# if the player has already taken one of his opponent's pieces and don't want to take another
		elif self.play_again == True :

			self.end_turn()
			
		# finally, the player may just want to unselect his piece, or want to try something impossible
		else :

			self.highlight = []
		


	# moving the selected piece on the board
	def move_on_grid (self, x, y) :

		self.grid[x][y] = self.grid[self.highlight[0]][self.highlight[1]]   # moving the piece
		self.grid[self.highlight[0]][self.highlight[1]] = 0					# and leaving a blank where it comes from

		self.last_moved = [x,y]

		if [self.highlight[0],self.highlight[1]] in self.queens :			# if a queen has moved
			self.queens.remove([self.highlight[0],self.highlight[1]])		# we need to update the queen positions
			self.queens.append([x,y])
			#print "A queen has been moved !"
		
		else :
			self.check_queen(x,y)   										# else, we may check if this piece has become a queen



	# special method called if a queen has made a takeover
	def queen_takeover (self,x,y) :

		done = False
		i = self.highlight[0]
		j = self.highlight[1]

		while (i!=x or j!=y) and done == False :

			if self.grid[i][j] > 0 :
				self.grid[i][j] = 0
				done = True
				if [i,j] in self.queens :
					self.queens.remove([i,j])

			i = i + (x-i)/abs(x-i)
			j = j + (y-j)/abs(y-j)



	# checking a possible huff
	def check_huff (self, x, y) :

		#print self.moves, self.takeovers, self.takeover_done, x, self.last_moved[0], y, self.last_moved[1]

		# conditions for a huff : 
		# - the selected piece can do a takeover
		# - the previous player hasn't made a takeover during his last turn
		# - the selected piece isn't the last that has been moved (meaning the player hasn't yet been able to do the takeover)
		# OR
		# - the last piece that has been moved could have done a takeover instead
		if (self.takeovers != [] and self.takeover_done == False and (x != self.last_moved[0] or y != self.last_moved[1]) and self.grid[x][y] != 0) or ([x,y] == self.possible_huff) :

			if [x,y] in self.queens :
				self.queens.remove([x,y])
				#print self.queens
			self.grid[x][y] = 0
			self.huff_done = True
			self.possible_huff = []



	# checking if a new queen has appeared
	def check_queen (self,x,y) :

		if self.player == 1 :
			if y == self.height-1 and [x,y] not in self.queens :
				self.queens.append([x,y])
				#print "New queen in town !"

		if self.player == 2 :
			if y == 0 and [x,y] not in self.queens :
				self.queens.append([x,y])
				#print "New queen in town !"
			


	# ending the player's turn (i.e. switching players and cleaning all temporary variables)
	def end_turn (self) :

		# if self.player == 1 :
		# 	self.player = 2

		# else :
		# 	self.player = 1
		self.player_end_turn = True

		self.moves = []
		self.highlight = []
		self.takeovers = []
		self.huff_done = False
		self.play_again = False

		#print("Turn has ended.")





	def possibilities (self, x, y) :


		self.moves = []
		self.takeovers = []


		# if a standard piece is selected
		if [x,y] not in self.queens :



			if self.grid[x][y] == 1 :


				if x-1 > -1 and y-1 > -1 :

					if self.grid[x-1][y-1] == 2 and x-2 > -1 and y-2 > -1 :

						if self.grid[x-2][y-2] == 0 :

							self.takeovers.append([x-2,y-2])
							#print "Ce pion peut prendre celui à l'arrière gauche."


				if x+1 < 10 and y-1 > -1 :

					if self.grid[x+1][y-1] == 2 and x+2 < 10 and y-2 > -1 :

						if self.grid[x+2][y-2] == 0 :

							self.takeovers.append([x+2,y-2])
							#print "Ce pion peut prendre celui à l'arrière droit."


				if x-1 > -1 and y+1 < 10 :

					if self.grid[x-1][y+1] == 0 and self.player == 1 :

						self.moves.append([x-1,y+1])
						#print "Ce pion peut être déplacé à l'avant gauche."

					elif self.grid[x-1][y+1] == 2 and x-2 > -1 and y+2 < 10 :

						if self.grid[x-2][y+2] == 0 :

							self.takeovers.append([x-2,y+2])
							#print "Ce pion peut prendre celui à l'avant gauche."



				if x+1 < 10 and y+1 < 10 :

					if self.grid[x+1][y+1] == 0 and self.player == 1 :

						self.moves.append([x+1,y+1])
						#print "Ce pion peut être déplacé à l'avant droit."

					elif self.grid[x+1][y+1] == 2 and x+2 < 10 and y+2 < 10 :

						if self.grid[x+2][y+2] == 0 :

							self.takeovers.append([x+2,y+2])
							#print "Ce pion peut prendre celui à l'avant droit."



			if self.grid[x][y] == 2 :


				if x-1 > -1 and y-1 > -1 :

					if self.grid[x-1][y-1] == 0 and self.player == 2 :

						self.moves.append([x-1,y-1])
						#print "Ce pion peut être déplacé à l'avant gauche."

					elif self.grid[x-1][y-1] == 1 and x-2 > -1 and y-2 > -1 :

						if self.grid[x-2][y-2] == 0 :

							self.takeovers.append([x-2,y-2])
							#print "Ce pion peut prendre celui à l'avant gauche."


				if x+1 < 10 and y-1 > -1 :

					if self.grid[x+1][y-1] == 0 and self.player == 2 :

						self.moves.append([x+1,y-1])
						#print "Ce pion peut être déplacé à l'avant droit."

					elif self.grid[x+1][y-1] == 1 and x+2 < 10 and y-2 > -1 :

						if self.grid[x+2][y-2] == 0 :

							self.takeovers.append([x+2,y-2])
							#print "Ce pion peut prendre celui à l'avant droit."


				if x-1 > -1 and y+1 < 10 :

					if self.grid[x-1][y+1] == 1 and x-2 > -1 and y+2 < 10 :

						if self.grid[x-2][y+2] == 0 :

							self.takeovers.append([x-2,y+2])
							#print "Ce pion peut prendre celui à l'arrière gauche."


				if x+1 < 10 and y+1 < 10 :

					if self.grid[x+1][y+1] == 1 and x+2 < 10 and y+2 < 10 :

						if self.grid[x+2][y+2] == 0 :

							self.takeovers.append([x+2,y+2])
							#print "Ce pion peut prendre celui à l'arrière droit."



		# if a queen is selected
		else :

			obstacle = False
			takeover = False
			i = x-1
			j = y-1

			while i>-1 and j>-1 and obstacle == False :

				if self.grid[i][j] == self.grid[x][y] :
					obstacle = True


				elif self.grid[i][j] > 0 :

					if i-1>-1 and j-1>-1 and takeover == False :
						if self.grid[i-1][j-1] == 0 :
							self.takeovers.append([i-1,j-1])
							takeover = True
							i = i-1
							j = j-1
						else :
							obstacle = True
					else :
						obstacle = True


				elif self.grid[i][j] == 0 :

					if takeover == False :
						self.moves.append([i,j])
					else :
						self.takeovers.append([i,j])

				i = i-1
				j = j-1



			obstacle = False
			takeover = False
			i = x+1
			j = y-1

			while i<10 and j>-1 and obstacle == False :

				if self.grid[i][j] == self.grid[x][y] :
					obstacle = True


				elif self.grid[i][j] > 0 :

					if i+1<10 and j-1>-1 and takeover == False :
						if self.grid[i+1][j-1] == 0 :
							self.takeovers.append([i+1,j-1])
							takeover = True
							i = i+1
							j = j-1
						else :
							obstacle = True
					else :
						obstacle = True


				elif self.grid[i][j] == 0 :

					if takeover == False :
						self.moves.append([i,j])
					else :
						self.takeovers.append([i,j])

				i = i+1
				j = j-1



			obstacle = False
			takeover = False
			i = x-1
			j = y+1

			while i>-1 and j<10 and obstacle == False :

				if self.grid[i][j] == self.grid[x][y] :
					obstacle = True


				elif self.grid[i][j] > 0 :

					if i-1>-1 and j+1<10 and takeover == False :
						if self.grid[i-1][j+1] == 0 :
							self.takeovers.append([i-1,j+1])
							takeover = True
							i = i-1
							j = j+1
						else :
							obstacle = True
					else :
						obstacle = True


				elif self.grid[i][j] == 0 :

					if takeover == False :
						self.moves.append([i,j])
					else :
						self.takeovers.append([i,j])

				i = i-1
				j = j+1



			obstacle = False
			takeover = False
			i = x+1
			j = y+1

			while i<10 and j<10 and obstacle == False :

				if self.grid[i][j] == self.grid[x][y] :
					obstacle = True


				elif self.grid[i][j] > 0 :

					if i+1<10 and j+1<10 and takeover == False :
						if self.grid[i+1][j+1] == 0 :
							self.takeovers.append([i+1,j+1])
							takeover = True
							i = i+1
							j = j+1
						else :
							obstacle = True
					else :
						obstacle = True


				elif self.grid[i][j] == 0 :

					if takeover == False :
						self.moves.append([i,j])
					else :
						self.takeovers.append([i,j])

				i = i+1
				j = j+1


	def check_end (self) :

		i = 0
		self.end = True
		while i < len(self.grid) and self.end == True :
			if 1 in self.grid[i] :
				self.end = False
			i = i+1

		if self.end == False :

			i = 0
			self.end = True
			while i < len(self.grid) and self.end == True :
				if 2 in self.grid[i] :
					self.end = False
				i = i+1


	def partie_en_cours(self) :

		send_sthg(self.sockets[self.player],["method","self.play()"])
		send_sthg(self.sockets[3-self.player],["method","self.wait()"])
		#send méthode: loop (afficher "à ton tour de jouer") JOUEUR C   -> done
		#send méthode: wait, JOUEUR QUI ATTEND   -> done

		coords = self.handle(recv_sthg(self.sockets[self.player]))
		#recv identifiant; x; y   -> done

		self.left_click(coords[0], coords[1])

		#On vérifie si la partie est terminée
		self.check_end()

		if self.end == True :

			send_sthg(self.sockets[3-self.player],["method","self.win()"])
			send_sthg(self.sockets[self.player],["method","self.lose()"])	




	def handle (self, message) :

		if "coords" in message :

			coords = unstring_coords(message[1+message.index("coords")])

		else :

			pass
			# TODO (?)

		return coords


def unstring_coords (coords) :

	rebuilt_coords = []
	temp = re.split("\[|\]|,",coords)

	for element in temp :

		if element not in ['', ' ','\t'] :
			rebuilt_coords.append(int(element))

	return rebuilt_coords


def send_sthg(sock, msg):

	final_msg = "$;"

	for element in msg :

		final_msg += str(element) + ";"

	final_msg += "$"

	sock.sendall(final_msg)
	ok=False
	while not ok:
		data=sock.recv(1024)
		if 'ok' in data:
			ok=True


def recv_sthg(sock):

	msg = sock.recv(4096)

	mess=msg.split(";")
	if mess[0] == "$" and mess[-1] == "$":
		mess.pop(0)
		mess.pop(-1)
		sock.sendall('$ok$')
		return mess

	else: 
		print 'ERROR'


def main_serveur(socket_1, ip1, socket_2, ip2) :
	
	#Creation de la partie
	partie = Board(socket_1,socket_2)

	#send à chaque joueur joueur1/joueur2
	socket_1.sendall("player1")
	ok=False
	while not ok:
		data=socket_1.recv(1024)
		if 'ok' in data:
			ok=True

	socket_2.sendall("player2")
	ok=False
	while not ok:
		data=socket_2.recv(1024)
		if 'ok' in data:
			ok=True

	send_sthg(socket_1,["method","self.draw_grid_1(grid)","grid",partie.grid])
	send_sthg(socket_2,["method","self.draw_grid_2(grid)","grid",partie.grid])

	print "Let's go !"

	while not partie.end:

		partie.partie_en_cours()


# def wait(number, ip) :

# 	print "Waiting for 2 players"
# 	ip[0].sendall("En attente d'un second joueur \n")
# 	while stop[number]:
# 		pass



######################################################################
######################################################################



s=socket(AF_INET,SOCK_STREAM)
s.setsockopt(SOL_SOCKET, SO_REUSEADDR,1)
s.bind(("",4242))
#serversocket.bind((socket.gethostname(), 80))

#PRENDRE EN COMPTE LE CAS OU LE JOUEUR IMPAIR SE DECONNECTE AVANT L'ARRIVEE DU JOUEUR PAIR

shutdown = False

threads = []

try :

	while shutdown == False :

		s.listen(5)
		print "Waiting for someone."
		(socket_1, (ip1,port)) = s.accept()
		socket_1.sendall("Waiting for an opponent.")
		print "Waiting for someone else."
		(socket_2, (ip2,port2)) = s.accept()
		socket_2.sendall("Waiting for an opponent.")
		newthread = Thread(target=main_serveur,args=(socket_1,ip1,socket_2,ip2))
		threads.append(newthread)
		newthread.start()


finally :
	
	for t in threads :
		t.join()

	s.close()

# s.listen(5)
# threads_wait = {}
# threads_play = []
# ip = {}
# global stop
# stop = {}
# global number
# number = 0

# try:
	
# 	while True:

# 		stop[number] = False
# 		(Newsock, (Newip, Newport)) = s.accept()
# 		ip[number] = [Newsock, Newip]
# 		my_thread = threading.Thread(target=wait, args=(number,ip[number]))
# 		my_thread.start()
# 		threads_wait[number] = my_thread
# 		number += 1


# 		if len(threads_wait) >= 2 :			

# 			temp = min(stop.keys())
# 			print temp,ip
# 			ip[temp][0].sendall("Opponent_found \n")
# 			ip1 = ip.pop(temp)
# 			del stop[temp]
# 			threads_wait[temp].join()
# 			del threads_wait[temp]

# 			temp = min(stop.keys())
# 			ip[temp][0].sendall("Opponent_found \n")
# 			ip2 = ip.pop(temp)
# 			del stop[temp]
# 			threads_wait[temp].join()
# 			del threads_wait[temp]

# 			my_thread_play=threading.Thread(target=main_serveur, args=(ip1,ip2))
# 			print "blablabla"
# 			threads_play.append(my_thread_play)




# finally:

# 	for t in threads_play:
# 		t.join()

# 	s.close() 