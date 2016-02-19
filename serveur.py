# -*- coding: utf-8 -*

import signal
import time
import sys
import os
import re
import errno
from socket import*
from threading import*



class Board :

	def __init__ (self, sock1, sock2) :

		self.height = 10
		self.width = 10
		self.grid = [[-1 for i in xrange(0,self.height,1)] for j in xrange(0,self.width,1)]

		self.init_board() 				# putting all pieces at their starting places


		# variables holding the state of the game
		self.sockets = {1:sock1,2:sock2}
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

		self.winner = None



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





	def left_click (self, x, y) :
		# there are 2 possibilities : whether the player wants to select a piece or to move it

		if self.highlight == [] :					# if no piece is already selected (selecting a piece to move or huffing an opponent's one)
			self.select(x,y) 						# we call the "select" method in the game engine
														
		else :										# else the player wants to move a piece
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

			if self.player == 1 :
				send_sthg(self.sockets[self.player],["method","self.highlight_piece_1(coords)","coords",self.highlight])
			else :
				send_sthg(self.sockets[self.player],["method","self.highlight_piece_2(coords)","coords",self.highlight])
			#send highlight_piece_1/2, highlight 	JOUEUR COURANT (self.player)


		elif self.player_end_turn :
			self.player = 3-self.player
			self.player_end_turn = False



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

				# if the player has selected one of his pieces (in order to move it)
				elif self.grid[x][y] == self.player :

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

		try :

			# Telling whose it is to play
			send_sthg(self.sockets[self.player],["method","self.play()"])

			# Waiting for coordinates of player click on grid
			coords = None
			while coords == None :
				coords = self.handle(recv_sthg(self.sockets[self.player]))

			# Handling client click and updating game status accordingly
			self.left_click(coords[0], coords[1])

			# Checking if the game has ended (win of one player)
			self.check_end()

			# if so
			if self.end == True :

				# the winner is not the current player (the current player is changed before checking for end conditions)
				send_sthg(self.sockets[3-self.player],["method","self.win()"])
				send_sthg(self.sockets[self.player],["method","self.lose()"])

				# self.winner used to update scores
				self.winner = 3-self.player	


		# catching an exception while running the game (client disconnection)
		except IOError :

			print "A client crashed."
			print "It's the player", str(self.player)
			# raising the exception, along with whose player has disconnected (it's necessarily the current player as we only talk to him)
			raise IOError(str(self.player))



	# handling any received message
	def handle (self, message) :

		# the message whether contains the coordinates of the click on grid
		if "coords" in message :

			coords = unstring_coords(message[1+message.index("coords")])
			return coords

		# or a simple ping sent by the client to tell he's still there
		elif "ping" in message :

			#print "ping'd"
			send_sthg(self.sockets[3-self.player],["ping"])
			return None

		# other cases should not happen, except if the message has been corrupted
		else :

			print "I have an issue in handling this message ! Trying to continue."

		return None



# translating string received to list of coordinates
def unstring_coords (coords) :

	rebuilt_coords = []
	temp = re.split("\[|\]|,",coords)

	for element in temp :

		if element not in ['', ' ','\t'] :
			rebuilt_coords.append(int(element))

	return rebuilt_coords



# sending a message with the built-in protocol
def send_sthg(sock, msg):

	# adding two '$' as delimiters
	final_msg = "$;"

	for element in msg :

		# each element is separated by ';'
		final_msg += str(element) + ";"

	final_msg += "$"


	try:
		sock.sendall(final_msg)
		ok=False
		while not ok:
			data=sock.recv(1024)
			if 'ok' in data:
				ok=True
			else:
				sock.sendall(final_msg)

	except timeout as e :

		raise IOError
	


# receiving a message with the built-in protocol
def recv_sthg(sock):

	try :

		msg = sock.recv(4096)

		mess=msg.split(";")
		if mess[0] == "$" and mess[-1] == "$":
			mess.pop(0)
			mess.pop(-1)
			sock.sendall('$ok$')
			return mess

		else:
			print 'Caught an unconsistent message :', msg
			print "Trying to continue."
			raise IOError

	except error as e :

		if e.errno==errno.ECONNRESET :
			print "Client disconnected."
			raise IOError

	except timeout as e :

		print "Timeout."
		raise IOError
	




def main_serveur(player1, player2) :
	

	try :

		try :

			sock1 = player1.sock
			sock2 = player2.sock
			# Initiating the board
			partie = Board(sock1,sock2)

			# Sending to both players their IDs (player1 or player2)
			send_sthg(sock1,["player1"])
			send_sthg(sock2,["player2"])

			# Initial drawing of the grid
			send_sthg(sock1,["method","self.draw_grid_1(grid)","grid",partie.grid])
			send_sthg(sock2,["method","self.draw_grid_2(grid)","grid",partie.grid])


			# Main loop running until the game ends
			while not partie.end:

				partie.partie_en_cours()

			# at the end of the match, we calculate the updated scores for both players
			update_scores(partie.winner,player1,player2)

			# asking the players if they want to play again
			send_sthg(sock1,["play_again"])
			again = recv_sthg(sock1)

			# if they don't, we remember it, in order to delete the corresponding object after
			if again != None :

				if int(again[0]) == 0 :
					player1.ready = False      # defaults to True

				# if they want to play again, we add them to the queue
				else :
					queue.append(player1)

			else :

				print "Couldn't get the answer from player1, trying to continue."


			send_sthg(sock2,["play_again"])
			again = recv_sthg(sock2)

			if again != None :

				if int(again[0]) == 0 :
					player2.ready = False
				else :
					queue.append(player2)

				print "Game ended normally."

			else :

				print "Couldn't get the answer from player2, trying to continue."


		# if a player disconnects while the game is running, it's considered as a loss (and his opponent wins the game)
		except IOError as e:

			# if a player has been disconnected (it can also be a different exception we don't know about)
			if len(str(e)) < 2 :

				# e : player that has been disconnected
				survivor = 3-int(str(e))    # ID of the remaining player
				send_sthg(partie.sockets[survivor],["method","self.win()"])

				# asking the survivor if he wants to play again
				send_sthg(partie.sockets[survivor],["play_again"])
				again = recv_sthg(partie.sockets[survivor])

				# if he doesn't, we remember it, in order to delete the corresponding object after
				if int(again[0]) == 0 :
					if survivor==1:
						player1.ready = False      # defaults to True
					else:
						player2.ready = False

				# if he wants to play again, we add him to the queue
				else :
					if survivor==1:
						queue.append(player1)
					else:
						queue.append(player2)

				update_scores(survivor,player1,player2)

				print "Game ended with a disconnection."



	# if something unexpected happens during while the game is running, or in the 'except' method above (e.g. if both players have disconnected one after the other)
	except StandardError as e :

		# sort of recurrent error
		if type(e) == TypeError :

			print "Something went wrong with the sockets, caught 'Type Error', as follows :"
			print e

		else :

			print "Something went wrong with the sockets, caught the following error :"
			print e

		print "Game ended poorly."

		# checking which player(s) is/are still there (if there's any)
		try :
			sock1.sendall("Check.")

		except :
			player1.ready = False

		try :
			sock2.sendall("Check.")

		except :
			player2.ready = False


		# if only one player is remaning, it's declared as winner
		if player1.ready and not player2.ready :
			update_scores(player1,player1,player2)

		elif player2.ready and not player1.ready :
			update_scores(player1,player1,player2)

		# each remaining player is added to the queue 
		#(we assume they still want to play, we know it's not a disconnection from their side that has caused the exception here)
		if player1.ready :
			queue.append(player1)

		if player2.ready :
			queue.append(player2)


	# in case it's needed, but it shouldn't be
	except KeyboardInterrupt as e :

		print "You tried an awkward interruption."
		#sys.exit(-1)




# -__-__-__-__-__-__-__-__-__-__-     Score Methods     -__-__-__-__-__-__-__-__-__-__- #


def update_scores (winner, player1, player2) :

	update_Elo(winner,player1.login,player2.login)
	
	# one more match has been played
	all_scores[player1.login][1] += 1
	all_scores[player2.login][1] += 1

	# updating player objects
	player1.score = all_scores[player1.login][0]
	player2.score = all_scores[player2.login][0]
	player1.nb_matches = all_scores[player1.login][1]
	player2.nb_matches = all_scores[player2.login][1]


def update_Elo (winner, login1, login2) :

	# current Elos
	Elo1 = all_scores[login1][0]
	Elo2 = all_scores[login2][0]

	# current number of matches played
	m1 = all_scores[login1][1]
	m2 = all_scores[login2][1]

	if m1 < 70 :
		k1 = 80.0 / (1+0.1*m1)
	else :
		k1 = 10
	if m2 < 70 :
		k2 = 80.0 / (1+0.1*m2)
	else :
		k2 = 10

	prob = 1 / (1 + 10**((Elo1-Elo2)/400.0))

	# calculating new Elos
	if winner == 1 :
		Elo1 += k1 * (1 - (1-prob))
		Elo2 += k2 * (0 - prob)

	else :
		Elo1 += k1 * (0 - (1-prob))
		Elo2 += k2 * (1 - prob)

	# updating scores in dictionary
	all_scores[login1][0] = Elo1
	all_scores[login2][0] = Elo2


# -__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__- #



# -__-__-__-__-__-__-__-__-__-     Matchmaking Method      -__-__-__-__-__-__-__-__-__- #


def trymatch (player1, player2) :

	return abs(player1.score-player2.score)/player1.queue_timer


# -__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__- #





##############################################################################################################################################################
##################################                                   class Online_Player                                    ##################################
##############################################################################################################################################################

class Online_Player :

	def __init__ (self, sock, ip, login, pw, score, nb_matches) :

		self.sock = sock                 # socket between client and server
		self.ip = ip                     # ip adress
		self.port = port				 # socket port
		self.login = login               # account info : login
		self.pw = pw                     # account info : password
		self.score = score               # Elo score
		self.nb_matches = nb_matches     # matches played
		self.queue_timer = 1             # how many 20 seconds he has already waited for an opponent ? (1=0s,2=30s,3=1min,4=1min30s...)
		self.queue_matchmaking = {}      # matchmaking scores to other players, with their login as key
		self.ready = True                # becomes False if he chooses not to play again after his first match


##############################################################################################################################################################
##############################################################################################################################################################


# loading account informations for all players in a dictionary, along with their scores in another
try :

	accounts = open("accounts.txt","r")

except :

	print "Couldn't find file 'accounts.txt'"
	sys.exit(1)

try :

	scores = open("scores.txt","r")

except :

	print "Couldn't find file 'scores.txt'"
	sys.exit(1)

temp = (accounts.read()).split("\r")
temp.pop()

all_accounts = {}
for i in temp :
	temp2 = i.split(";")
	all_accounts[temp2[0]] = temp2[1]
print all_accounts

temp = (scores.read()).split("\r")
temp.pop()

all_scores = {}
for i in temp :
	temp2 = i.split(";")
	all_scores[temp2[0]] = [float(temp2[1]),int(temp2[2])]
print all_scores


# -__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-      Signal methods      -__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__- #

def handler(signum, frame) :

    #print 'Signal handler called with signal', signum

    if signum == 14 :
    	raise RuntimeError("20 seconds have passed.")
    else :
    	raise RuntimeError("Some threads are taking too long to stop. Enabling forced shutdown.")


def quit_handler(signal, frame):
	print 'Quitting.'
	raise KeyboardInterrupt("Out !")

signal.signal(signal.SIGINT, quit_handler)


# -__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__- #


# -__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-       Removing offline players       -__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__- #

def remove_disc() :

	# checking if there are disconnected players (or that don't want to play again)
	for player in online_players :

		# if so
		if player.ready == False :

			if player in queue :
				queue.remove(player)

			online_players.remove(player)
			# the corresponding socket is closed
			player.sock.shutdown(SHUT_WR)
			player.sock.close()
			# and the player object is deleted
			del player


# -__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__- #



setdefaulttimeout(40.0)    # default timeout for all communications between clients and servers
s=socket(AF_INET,SOCK_STREAM)
s.setsockopt(SOL_SOCKET, SO_REUSEADDR,1)
s.bind(("127.0.0.1",4242))
s.listen(16)

guests_number = 0
threads = []
queue = []
online_players = []


# -__-__-__-__-__-__-     Signals    -__-__-__-__-__-__- #

signal.signal(signal.SIGALRM,handler)
signal.setitimer(signal.ITIMER_REAL,20,20)


#############################################
#                 Main script               #
#############################################

"""
Behaviour : The server constantly look for clients and try to match them with a player in the queue (if their respective Elos are close enough).
If it manages to do it, a game is started in a separate thread with the 2 players.
Else, the newcomer is added to the queue.
Moreover, every 20 seconds, the server tries to match players in queue with each other by allowing a larger difference in Elos, growing as (waiting) time passes.
Finally, it checks once in a while (everytime a new player joins, or 20 seconds have passed) if there are disconnected players.
The associated objects are deleted if so.
"""

try :

	# could be replaced in the future by 'while shutdown == False' or something similar to handle server shutdown (voluntary or not)
	while True :

		account_infos = None

		# looking for a player
		while not account_infos :

			print "Waiting for someone."

			# checking if there are disconnected players (or that don't want to play again)
			remove_disc()


			# looking for a new client (player)
			# 20 seconds are allowed for this. 
			# If it takes longer (i.e. no new player wants to join), we try to match players who are waiting for an opponent, to prevent them for potentially waiting forever.
			try :

				(sock, (ip,port)) = s.accept()


			# if it indeed took longer
			except RuntimeError as e :

				print e
				remove_disc()

				# each player still in queue have been waiting 20 seconds more since last time, so we increase their timers
				for wp in queue :

					wp.sock.sendall("ping")

					wp.queue_timer += 1

				# if there are at least 2 players in queue, we evaluate their matchmaking score (difference of Elos modulated by how long they've been waiting)
				if len(queue) >= 2 :

					for wp1 in queue :

						for wp2 in queue :

							if wp1 != wp2 :

								wp1.queue_matchmaking[wp2.login] = trymatch(wp1,wp2)
						
						# if one of the scores is low enough, it means the players are close enough in level to be matched together (or there is no better opponent)
						if min(wp1.queue_matchmaking.values()) < 50 :

							# getting the closest player
							opponent_login = min(wp1.queue_matchmaking,key=wp1.queue_matchmaking.get)

							for wp2 in queue :
								if wp2.login == opponent_login :
									opponent = wp2
									break

							# we can then remove both players from the queue
							queue.remove(wp1)
							queue.remove(opponent)
							wp1.queue_timer = 1
							opponent.queue_timer = 1
							wp1.queue_matchmaking = {}
							opponent.queue_matchmaking = {}							

							# once both players have been found, we can effectively create the game
							newthread = Thread(target=main_serveur,args=(wp1,opponent))
							threads.append(newthread)
							newthread.start()
							# print "Game started, currently ",len(threads)," threads have been created."


			# if a new player wants to join
			else :

				login,pw,new = sock.recv(4096).split(";")         # getting the account informations he transmitted
				new = int(new)

				if login == "guest" :                             # if he wants to play as a guest (no account creation, no scores remembered)
					login = "".join(["guest",str(guests_number)]) # we give him a temporary account, like 'guest17' if it is the 17th one since the launch of the server
					guests_number += 1

				if new :                                          # if it is a new player, we create an account for him
					all_accounts[login] = pw
					account_infos = [login,pw]
					all_scores[login]= [500]                      # Elo initial rating
					all_scores[login].append(0)                   # number of matches played
					sock.sendall("Ok")

				elif login not in all_accounts.keys() :           # if the player says he already has an account, we check if he entered the right login

					sock.sendall("Wrong")
					sock.shutdown(SHUT_WR)
					sock.close()
					break

				else :
					if all_accounts[login] != pw :                # and the right password
						sock.sendall("Wrong")
						sock.shutdown(SHUT_WR)
						sock.close()
						break

					else :
						account_infos = [login,pw]
						sock.sendall("Ok")



				# if everything's okay, we try here to match this new player with any player in queue (waiting for an opponent)
				# creating first the object representing the player
				newcomer = Online_Player(sock, ip, login, pw, all_scores[login][0], all_scores[login][1])
				# and adding it to the list of online players
				online_players.append(newcomer)

				# if there's at least one player waiting, matchmaking process is exactly the same as above
				if queue != [] :

					for waiting_player in queue :

						newcomer.queue_matchmaking[waiting_player.login] = trymatch(waiting_player,newcomer)


					if min(newcomer.queue_matchmaking.values()) < 50 :

						opponent_login = min(newcomer.queue_matchmaking,key=newcomer.queue_matchmaking.get)

						for wp2 in queue :
							if wp2.login == opponent_login :
								opponent = wp2
								break

						queue.remove(opponent)
						opponent.queue_timer = 1
						opponent.queue_matchmaking = {}

						# once both players have been found, we can effectively create the game
						newthread = Thread(target=main_serveur,args=(newcomer,opponent))
						newthread.daemon = True
						threads.append(newthread)
						newthread.start()
						# print "Game started, currently ",len(threads)," threads have been created."

					# if there isn't any player in queue whose level is close enough to the newcomer, the newcomer is added to the queue
					else :

						queue.append(newcomer)

				# if there's noone in queue, the newcomer is added to it
				else :

					queue.append(newcomer)




except KeyboardInterrupt as e :

	print "You called for an emergency shutdown."

	sys.exit(-1)  # in case it's needed



# in case of an error or a voluntary shutdown, we need to make sure not all data (account infos + scores) is lost, so we save it in 2 files :
# (accounts.txt, scores.txt)
finally :

	signal.setitimer(signal.ITIMER_REAL,0)

	signal.alarm(500)


	for player in online_players :

		try :

			player.sock.sendall("shutdown")

		except :
			pass
	
	try :

		for t in threads :
			t.join(60)

	except RuntimeError as e :

		print e


	for player in online_players :

		online_players.remove(player)
		# the corresponding socket is closed
		player.sock.shutdown(SHUT_WR)
		player.sock.close()
		# and the player object is deleted
		del player

	signal.alarm(0)

	s.shutdown(SHUT_RDWR)
	s.close()


	accounts = open("accounts.txt","w")
	for i in all_accounts.keys() :

		if 'guest' not in i :
			accounts.write(";".join([i,all_accounts[i]]))
			accounts.write("\r")

	scores = open("scores.txt","w")
	for i in all_scores.keys() :

		if 'guest' not in i :
			to_write = i
			for j in xrange(0,2,1) :
				to_write += ";"+str(all_scores[i][j])

			scores.write(to_write)
			scores.write("\r")

