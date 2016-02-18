# -*- coding: utf-8 -*

from Tkinter import*
import tkMessageBox

import signal
import threading
import time
import sys
import os
import re
from socket import*

import tkDialog



# defines the popup window used for asking login informations to a player (not included in minimalistic popup windows package 'tkMessageBox')
class LoginWindow(tkDialog.Dialog):

	def body(self, master):

		Label(master, text="Login:").grid(row=0)
		Label(master, text="Password:").grid(row=1)

	 	self.e1 = Entry(master)
		self.e2 = Entry(master)

		self.e1.grid(row=0, column=1)
		self.e2.grid(row=1, column=1)
		return self.e1 # initial focus

	def apply(self):

		login = self.e1.get()
		pw = self.e2.get()
		self.result = [login, pw]



# defines a popup window type with a three-way choice through buttons (here used when first launching the game)
class LogRegGuestWindow(tkDialog.Ask3way):

	def body(self, master):

		Label(master, text="Already have an account ?").grid(row=0)
		return None 

	def apply_login(self):

		self.result = 1

	def apply_register(self):

		self.result = 2

	def apply_guest(self):

		self.result = 3





class Layout:

	def __init__(self, player_ID, serv_socket) :

		self.fenetre = Tk()
		self.fenetre.title("Super Crazy Checkers Deluxe 9000 (online)")
		

		self.h = self.fenetre.winfo_screenheight() * 0.5
		self.w = min(self.fenetre.winfo_screenwidth() * 0.5, 1.5*self.h)


		self.click = False 					# only used to exit play() method upon click
		self.my_turn = False				# preventing the client from sending coordinates on click when waiting for the opponent
		self.end_game = False				# used to exit run() when game has ended

		self.player_ID = player_ID			# this player's ID (either 1 or 2, determined by the server)

		self.serv_socket = serv_socket		# server socket



		self.plz_h = min(self.h,0.67*self.w)		# board height
		self.plz_w = self.plz_h						# board width

		self.length = 10            # number of cases on the board (10 for international (polish) checkers)

		# graphical parameters
		self.cs = (0.1*self.plz_h)-1			# square size (height and width)
		self.x_gap = 0.1*self.cs 				# x gap between 2 squares
		self.y_gap = 0.1*self.cs				# y gap between 2 squares
		self.size = self.cs - self.x_gap 		# piece size

		# parameters for the cemetery (place where we draw the pieces that have been taken)
		self.cemetery_cs = 0.3*self.cs
		self.cemetery_size = self.cemetery_cs - self.x_gap
		self.cemetery_y_gap = 1.22*self.cemetery_cs



		# Tkinter (graphical) objects
		world = PanedWindow(self.fenetre,height=self.h-1,width=self.w-1)
		self.playzone = Canvas(self.fenetre,height=self.plz_h-1,width=self.plz_w-1,bg='white')
		controls = PanedWindow(self.fenetre,height=self.plz_h-1,width=self.w-self.plz_w,orient=VERTICAL)

		self.playzone.create_rectangle(1,1,self.plz_h-2,self.plz_w-2)


		# label indicating the player whose turn it is
		self.player_now = StringVar()
		self.player_now.set("Now playing : Green")
		label_player = Label(controls,textvariable=self.player_now,height=4)

		controls.add(label_player)


		# canvas to draw the pieces taken by opponent
		self.cemetery = Canvas(controls,height=100)

		controls.add(self.cemetery)


		world.add(self.playzone)
		world.add(controls)
		world.pack()


		# event listener for left clicks on board
		self.playzone.bind("<Button-1>", self.left_click)





	def ping (self) :

		print 'Pinging'
		send_sthg(self.serv_socket,["ping"])

		self.ticktock = 2
		#print "finished",self.ticktock



	def play (self) :

		#print "Your turn!"
		self.my_turn = True
		self.click = False
		self.ticktock = 1

		while not self.click :

			t = threading.Timer(30.0,self.ping)
			t.daemon = True
			t.start()
			#print "started A",self.ticktock

			while self.ticktock == 1 and not self.click :

				self.fenetre.update_idletasks()
				self.fenetre.update()

			self.ticktock = 1


		t.cancel()

		#print "Out of play()"
		self.my_turn = False




	def win (self) :

		tkMessageBox.showinfo("SCCD9", "Congratulations! You won!")
		self.end_game = True

	def lose (self) :

		tkMessageBox.showinfo("SCCD9", "You lost! Maybe next time!")
		self.end_game = True



	# drawing the grid with player 1 below
	def draw_grid_1 (self, grid, queens = []) :

		self.playzone.delete("all")
		for i in xrange (len(grid)) :
			for j in xrange (len(grid)) :
				if grid[i][j] == -1 :
					self.playzone.create_oval(self.plz_w-(self.cs*i+self.x_gap),self.plz_h-(self.cs*j+self.y_gap),self.plz_w-(self.cs*i+self.x_gap+self.size),self.plz_h-(self.cs*j+self.y_gap+self.size),outline='white')
				else :
					self.playzone.create_oval(self.plz_w-(self.cs*i+self.x_gap),self.plz_h-(self.cs*j+self.y_gap),self.plz_w-(self.cs*i+self.x_gap+self.size),self.plz_h-(self.cs*j+self.y_gap+self.size),outline='black')
				
				if grid[i][j] == 1 :
					self.playzone.create_oval(self.plz_w-(self.cs*i+self.x_gap+self.size/4),self.plz_h-(self.cs*j+self.y_gap+self.size/4),self.plz_w-(self.cs*i+self.x_gap+3*self.size/4),self.plz_h-(self.cs*j+self.y_gap+3*self.size/4),outline='#d00',fill='#d00')
					if [i,j] in queens :
						self.playzone.create_oval(self.plz_w-(self.cs*i+self.x_gap+self.size/16),self.plz_h-(self.cs*j+self.y_gap+self.size/16),self.plz_w-(self.cs*i+self.x_gap+15*self.size/16),self.plz_h-(self.cs*j+self.y_gap+15*self.size/16),outline='#d00',fill='#d00')

				if grid[i][j] == 2 :
					self.playzone.create_oval(self.plz_w-(self.cs*i+self.x_gap+self.size/4),self.plz_h-(self.cs*j+self.y_gap+self.size/4),self.plz_w-(self.cs*i+self.x_gap+3*self.size/4),self.plz_h-(self.cs*j+self.y_gap+3*self.size/4),outline='#080',fill='#080')
					if [i,j] in queens :
						self.playzone.create_oval(self.plz_w-(self.cs*i+self.x_gap+self.size/16),self.plz_h-(self.cs*j+self.y_gap+self.size/16),self.plz_w-(self.cs*i+self.x_gap+15*self.size/16),self.plz_h-(self.cs*j+self.y_gap+15*self.size/16),outline='#080',fill='#080')



	# drawing the grid with player 2 below
	def draw_grid_2 (self, grid, queens = []) :

		self.playzone.delete("all")
		for i in xrange(len(grid)) :
			for j in xrange(len(grid)) :
				if grid[i][j] == -1 :
					self.playzone.create_oval(self.cs*i+self.x_gap,self.cs*j+self.y_gap,self.cs*i+self.x_gap+self.size,self.cs*j+self.y_gap+self.size,outline='white')
				else :
					self.playzone.create_oval(self.cs*i+self.x_gap,self.cs*j+self.y_gap,self.cs*i+self.x_gap+self.size,self.cs*j+self.y_gap+self.size,outline='black')
				
				if grid[i][j] == 1 :
					self.playzone.create_oval(self.cs*i+self.x_gap+self.size/4,self.cs*j+self.y_gap+self.size/4,self.cs*i+self.x_gap+3*self.size/4,self.cs*j+self.y_gap+3*self.size/4,outline='#d00',fill='#d00')
					if [i,j] in queens :
						self.playzone.create_oval(self.cs*i+self.x_gap+self.size/16,self.cs*j+self.y_gap+self.size/16,self.cs*i+self.x_gap+15*self.size/16,self.cs*j+self.y_gap+15*self.size/16,outline='#d00',fill='#d00')

				if grid[i][j] == 2 :
					self.playzone.create_oval(self.cs*i+self.x_gap+self.size/4,self.cs*j+self.y_gap+self.size/4,self.cs*i+self.x_gap+3*self.size/4,self.cs*j+self.y_gap+3*self.size/4,outline='#080',fill='#080')
					if [i,j] in queens :
						self.playzone.create_oval(self.cs*i+self.x_gap+self.size/16,self.cs*j+self.y_gap+self.size/16,self.cs*i+self.x_gap+15*self.size/16,self.cs*j+self.y_gap+15*self.size/16,outline='#080',fill='#080')



	# drawing the cemetery (containing all pieces taken by the opponent)
	def draw_cemetery (self, grid, queens = []) :

		self.cemetery.delete("all")
		# number of pieces taken = 20 - pieces left - queens (as a queen worths 2 pieces)
		red_taken = 20 - sum([i.count(1) for i in grid]) - len([1 for i in queens if grid[i[0]][i[1]] == 1])
		green_taken = 20 - sum([i.count(2) for i in grid]) - len([1 for i in queens if grid[i[0]][i[1]] == 2])
		
		# drawing on 2 lines, for easier understanding
		for i in xrange(red_taken) :
			if i < 10 :
				self.cemetery.create_oval(self.cemetery_cs*i+self.x_gap,self.y_gap,self.cemetery_cs*i+self.x_gap+self.cemetery_size,self.y_gap+self.cemetery_size,outline='#d00',fill='#d00')
			else :
				self.cemetery.create_oval(self.cemetery_cs*(i-10)+self.x_gap,self.cemetery_y_gap+self.y_gap,self.cemetery_cs*(i-10)+self.x_gap+self.cemetery_size,self.y_gap+self.cemetery_y_gap+self.cemetery_size,outline='#d00',fill='#d00')

		for i in xrange(green_taken) :
			if i < 10 :
				self.cemetery.create_oval(self.cemetery_cs*i+self.x_gap,self.y_gap+2*self.cemetery_y_gap,self.cemetery_cs*i+self.x_gap+self.cemetery_size,self.y_gap+2*self.cemetery_y_gap+self.cemetery_size,outline='#080',fill='#080')
			else :
				self.cemetery.create_oval(self.cemetery_cs*(i-10)+self.x_gap,self.y_gap+3*self.cemetery_y_gap,self.cemetery_cs*(i-10)+self.x_gap+self.cemetery_size,self.y_gap+3*self.cemetery_y_gap+self.cemetery_size,outline='#080',fill='#080')



	def highlight_piece_1 (self, coords) :

		self.playzone.create_oval(self.plz_w-(self.cs*coords[0]+self.x_gap+self.size/6),self.plz_h-(self.cs*coords[1]+self.y_gap+self.size/6),self.plz_w-(self.cs*coords[0]+self.x_gap+5*self.size/6),self.plz_h-(self.cs*coords[1]+self.y_gap+5*self.size/6),outline='black')



	def highlight_piece_2 (self, coords) :

		self.playzone.create_oval(self.cs*coords[0]+self.x_gap+self.size/6,self.cs*coords[1]+self.y_gap+self.size/6,self.cs*coords[0]+self.x_gap+5*self.size/6,self.cs*coords[1]+self.y_gap+5*self.size/6,outline='black')



	# method called by a left click on board
	def left_click(self, event) :

		if self.my_turn == True :

			self.click = True

			# getting where the click has happened

			if self.player_ID == "player2" :
				x = int(event.x / (self.plz_h/self.length))
				y = int(event.y / (self.plz_w/self.length))

			else :
				x = int(10 - event.x/(self.plz_h/self.length))
				y = int(10 - event.y/(self.plz_w/self.length))

			send_sthg(self.serv_socket,["coords",[x,y]])




	def check_end (winner) :
		
		if winner =='player1':
			self.player_now.set("The red guy has won !")

		if winner =='player2':
			self.player_now.set("The green guy has won !")




	def run (self) :

		try :
			while not self.end_game :

				#print "Waiting for an order."
				message = recv_sthg(self.serv_socket)
				self.handle(message)
				self.fenetre.update_idletasks()
				self.fenetre.update()

		except IOError as e :
			raise

		except RuntimeError as e :
			raise


	def handle (self, message) :

		if "grid" in message :

			grid = unstring_grid(message[1+message.index("grid")])

		if "queens" in message :

			queens = unstring_queens(message[1+message.index("queens")])

		if "coords" in message :

			coords = unstring_coords(message[1+message.index("coords")])

		if message[0] == "method" :

			eval(message[1+message.index("method")])

		elif "ping" in message :

			print "ping'd"
			#pass
			# TODO (?)

			

def unstring_grid (grid) :

	rebuilt_grid = [[]]
	temp = re.split("\[|\]|,",grid)
	count = 0
	cur_line = 0

	for element in temp :

		if element in ['-1',' -1','0',' 0','1',' 1','2',' 2'] :
			rebuilt_grid[cur_line].append(int(element))
			count += 1

		if count == 10 and cur_line < 9 :
			rebuilt_grid.append([])
			cur_line += 1
			count = 0

	return rebuilt_grid



def unstring_queens (queens) :

	rebuilt_queens = [[]]
	temp = re.split("\[|\]|,",queens)
	count = 0
	cur_line = 0

	for element in temp :

		if element not in ['', ' ','\t'] :
			rebuilt_queens[cur_line].append(int(element))
			count += 1

		if count == 2 and cur_line < 0.25*(len(temp)-2)-1 :
			rebuilt_queens.append([])
			cur_line += 1
			count = 0

	if rebuilt_queens == [[]] :

		rebuilt_queens = []

	return rebuilt_queens



def unstring_coords (coords) :

	rebuilt_coords = []
	temp = re.split("\[|\]|,",coords)

	for element in temp :

		if element not in ['', ' ','\t'] :
			rebuilt_coords.append(int(element))

	return rebuilt_coords


def handler_com(signum, frame):

    print 'Signal handler called with signal', signum
    raise RuntimeError("Connection expired.")



def send_sthg(sock, msg):

	final_msg = "$;"

	for element in msg :

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

		print e
		raise IOError("Disconnected from server.")



def recv_sthg(sock):


	try :

		msg = sock.recv(4096)
		#print msg

		mess=msg.split(";")

		if "shutdown" in msg :

			print "Server will be unavailable in a few minutes. If you're currently in a game, please end it as soon as possible."
			mess.remove("shutdown")

			if mess == [] :

				msg = sock.recv(4096)
				mess = msg.split(";")

		if mess[0] == "$" and mess[-1] == "$":
			mess.pop(0)
			mess.pop(-1)
			sock.sendall('$ok$')
			return mess

		elif 'Check.' in msg :

			raise RuntimeError("Game crashed at server.")

		else :

			print 'Caught an unconsistent message :', msg
			sock.sendall('$errmsg$')

	except timeout as e :

		print e
		raise IOError("Disconnected from server.")
	




def main_client(player_ID, sC):

	try :

		Checkers = Layout(player_ID, sC)
		# print Checkers.player_ID

		Checkers.run()

		# once the game has ended, the player is asked (through a minimalistic popup window (from the package 'tkMessageBox')) to choose to play again or leave
		if tkMessageBox.askyesno("SCCD9", "Play again ?") :
			Checkers.fenetre.destroy()
			answer = 1

		else :
			Checkers.fenetre.destroy()
			answer = 0

		# we forward his choice to the server

		data = [""]
		while data[0] != "play_again" :
			data = recv_sthg(sC)

		send_sthg(sC,[str(answer)])
		#print "answer sent"			

		return answer


	except IOError as e :

		raise

	except RuntimeError as e :

		print e
		Checkers.fenetre.destroy()
		return 1




##############################################################################################################################################################
##############################################################################################################################################################


# -__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__- #
# -__-__-__-__-                                               Login, Register, or play as Guest                                                -__-__-__-__- #
# -__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__- #


mainwindow = Tk()
mainwindow.title("Super Crazy Checkers Deluxe 9000 (online)")
# creating the main window, and adapting its size to the user's screen
# this is a temporary one which gets destroyed as soon as the game starts
# it is only here for popup windows to work properly, and maybe for design purposes (what about adding a nice image/drawing as background ?)
background_pic = PhotoImage(file="background.gif")
sthg = PanedWindow(mainwindow, height=min(600,mainwindow.winfo_screenheight()*0.8), width=min(800,mainwindow.winfo_screenwidth()*0.8, 1.5*mainwindow.winfo_screenheight()*0.8))
#print mainwindow.winfo_screenheight()*0.8,mainwindow.winfo_screenwidth()*0.8
bg_label = Label(sthg, image=background_pic)
bg_label.image = background_pic
bg_label.place(x=0, y=0, relwidth=1, relheight=1)
sthg.add(bg_label)
sthg.pack()

# upon starting the game, the player can whether login to his account, create a new one, or play as guest (it means that his performance won't be remembered)
# these options are displayed through (not so fancy) popup windows
choice = None

while not choice :

	temp = LogRegGuestWindow(mainwindow,"Welcome")
	choice = temp.result

	if temp.result == 1 :
		temp2 = LoginWindow(mainwindow,"Login Window")
		infos = temp2.result
		infos.append(str(0))

	elif temp.result == 2 :
		temp2 = LoginWindow(mainwindow,"Register Window")
		infos = temp2.result
		infos.append(str(1))

	elif temp.result == 3 :
		infos = ['guest','None',str(1)]

	else :
		print "Error in Login !"
		sys.exit(0)

# when he joins the server, a player wants to play (so again != 0), but he hasn't played yet (so again != 1), I chose again = -1
again = -1

##########
try :

	setdefaulttimeout(45.0)
	# connecting to the server
	sC = socket(AF_INET,SOCK_STREAM)
	sC.connect(("127.0.0.1",4242))

	# and immediately sending account infos
	sC.sendall(";".join(infos))
	answer = sC.recv(1024)

	# if those infos are wrong, the program ends, and the player has to enter his account infos again
	if answer == "Wrong" :
		tkMessageBox.showwarning("SCCD9", "Invalid login/password combination. Please try again.")
		sC.shutdown(SHUT_WR)
		sC.close()
		sys.exit(0)


	# if they are right, we can go on
	else :

	# -__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__-__- #

		# as long as the person wants to play
		while again != 0 :

			opponent_found = False

			# waiting until an opponent is found
			while opponent_found == False :
				data = sC.recv(1024)
				if "player" in data :
					opponent_found = True
					sC.sendall('$ok$')
				elif "ping" in data :
					print "ping'd"

			# once found, the game can starts
			player_ID = data.split(";")[1]
			# so we hide the menu window
			mainwindow.withdraw()

			# and create the real game frame
			# this method returns 1 if the player has chosen to play one more game, and 0 if he decides to leave	
			again = main_client(player_ID, sC)

			# bringing back the menu window
			mainwindow.deiconify()	


except IOError as e :

	print e
	sC.shutdown(SHUT_WR)
	sC.close()
	sys.exit(-1)


except KeyboardInterrupt as e :

	print "Argh!"
	sC.shutdown(SHUT_WR)
	sC.close()
	sys.exit(-1)


else :

	sC.shutdown(SHUT_WR)
	sC.close()

print "See you !"