# -*- coding: utf-8 -*

from Tkinter import*
import time
import os
import re
import inspect
from socket import*

#import serveur #SCCD9


class Layout:

	def __init__(self,player_ID, serv_socket):

		self.fenetre = Tk()
		self.fenetre.title("Super Crazy Checkers Deluxe 9000 (v0.7)")
		self.fenetre.geometry("900x600")


		self.click = False
		self.my_turn=False

		self.player_ID=player_ID

		self.serv_socket=serv_socket

		# game engine : rules, pace...
		#self.game = SCCD9.Board()

		self.plz_h = 600			# board height
		self.plz_w = 600			# board width

		self.length = 10

		# graphical parameters
		self.cs = 59 				# square size (height and width)
		self.x_gap = 6 				# x gap between 2 squares
		self.y_gap = 6 				# y gap between 2 squares
		self.size = 54 				# piece size

		# parameters for the cemetery (place where we draw the pieces that have been taken)
		self.cemetery_cs = 18
		self.cemetery_size = 12
		self.cemetery_y_gap = 22



		# Tkinter (graphical) objects
		world = PanedWindow(self.fenetre,height=599,width=899)
		self.playzone = Canvas(self.fenetre,height=599,width=599,bg='white')
		controls = PanedWindow(self.fenetre,height=599,width=300,orient=VERTICAL)

		self.playzone.create_rectangle(1,1,598,598)


		# label indicating the player whose turn it is
		self.player_now = StringVar()
		self.player_now.set("Now playing : Green")
		label_player = Label(controls,textvariable=self.player_now,height=4)

		controls.add(label_player)


		# canvas to draw the pieces taken by opponent
		self.cemetery = Canvas(controls,height=100)

		controls.add(self.cemetery)


		# -__-__-__-__-__-__-__-__-__-__-__-__-__- deprecated -__-__-__-__-__-__-__-__-__-__-__-__-__- #
		# # auto-rotation checkbox
		# self.autorot = IntVar()
		# self.autorot.set(0)
		# check_autorot = Checkbutton(controls,text="Auto-rotate",variable=self.autorot,height=15)

		# controls.add(check_autorot)

		# # reset button (hopefully will after be included in a menu)
		# reset_button = Button(controls,text="Restart",command=self.reset)

		# controls.add(reset_button)
		# -__-__-__-__-__-__-__-__-__-__-__-__-__- deprecated -__-__-__-__-__-__-__-__-__-__-__-__-__- #


		world.add(self.playzone)
		world.add(controls)
		world.pack()


		# event listener for left clicks on board
		self.playzone.bind("<Button-1>", self.left_click)


		# -__-__-__-__- deprecated -__-__-__-__- #
		# # drawing the board for the first time
		# self.draw_grid_2(self.game.grid)
		# -__-__-__-__- deprecated -__-__-__-__- #


	def play(self):
		print "Your turn!"
		self.click = False
		while not self.click:
			self.fenetre.update_idletasks()
			self.fenetre.update()


	def wait(self):
		print "Wait!"
		recv_sthg(self.serv_socket) 


	# drawing the grid with player 1 below
	def draw_grid_1 (self, grid, queens = []) :

		print "truc"
		print grid
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




	# method called by a left click on board
	def left_click(self, event) :

		self.click = True

		# getting where the click has happened

		if self.player_ID == 2 :
			x = event.x / (self.plz_h/self.length)
			y = event.y / (self.plz_w/self.length)

		else :
			x = 9 - event.x/(self.plz_h/self.length)
			y = 9 - event.y/(self.plz_w/self.length)

		send_sthg(self.serv_socket,["coords", str([x,y])])


		#send identifiant_joueur, x, y 
		#recv draw_grid_1, grid, queens OU 	draw_grid_2, grid, queens
		#recv draw_cemetery, grid, queens	
		#recv highlight_piece_1, highlight 	OU NON
		#recv loop 							OU NON			

		# # updating the drawing of the grid
		# if self.game.player == 1 :
		# 	self.draw_grid_1(self.game.grid,self.game.queens)
		# else :
		# 	self.draw_grid_2(self.game.grid,self.game.queens)

		# self.draw_cemetery(self.game.grid,self.game.queens)


		# # and highlighting the currently selected piece
		# if self.game.highlight != [] :

		# 	if self.game.player == 1 :
		# 		self.highlight_piece_1(self.game.highlight)
		# 	else :
		# 		self.highlight_piece_2(self.game.highlight)


		# if self.game.player == 1 :
		# 	self.player_now.set("Now playing : Red")
		# else :
		# 	self.player_now.set("Now playing : Green")

		# self.check_end()


	def highlight_piece_1 (self, coords) :

		self.playzone.create_oval(self.plz_w-(self.cs*coords[0]+self.x_gap+self.size/6),self.plz_h-(self.cs*coords[1]+self.y_gap+self.size/6),self.plz_w-(self.cs*coords[0]+self.x_gap+5*self.size/6),self.plz_h-(self.cs*coords[1]+self.y_gap+5*self.size/6),outline='black')



	def highlight_piece_2 (self, coords) :

		self.playzone.create_oval(self.cs*coords[0]+self.x_gap+self.size/6,self.cs*coords[1]+self.y_gap+self.size/6,self.cs*coords[0]+self.x_gap+5*self.size/6,self.cs*coords[1]+self.y_gap+5*self.size/6,outline='black')



	# def check_end (self) :

	# 	i = 0
	# 	end = True
	# 	while i < self.length and end == True :
	# 		if 1 in self.game.grid[i] :
	# 			end = False
	# 		i = i+1

	# 	if end == True :
	# 		self.player_now.set("The green guy has won !")

	# 	i = 0
	# 	end = True
	# 	while i < self.length and end == True :
	# 		if 2 in self.game.grid[i] :
	# 			end = False
	# 		i = i+1

	# 	if end == True :
	# 		self.player_now.set("The red guy has won !")


	def check_end(winner):
		
		# if winner == 'nowinner':
		# 	break
		
		if winner =='player1':
			self.player_now.set("The red guy has won !")

		if winner =='player2':
			self.player_now.set("The green guy has won !")







	# -__-__-__-__-__- deprecated -__-__-__-__-__- #
	# def reset (self) :

	# 	self.fenetre.destroy()
	# 	os.system("python SCCD9_interface.py")
	# -__-__-__-__-__- deprecated -__-__-__-__-__- #



	# # (Tkinter's mainloop)
	# def click_loop (self) :

	# 	#afficher à ton tour de jouer
	# 	#self.fenetre.mainloop()
	# 	self.click = False
	# 	while not self.click:
	# 		self.fenetre.update_idletasks()
	# 		self.fenetre.update()


	def run (self) :

		while True :

			message=recv_sthg(self.serv_socket)
			self.handle(message)
			self.fenetre.update_idletasks()
			self.fenetre.update()


	def handle (self, message) :

		if "grid" in message :

			grid = unstring_grid(message[1+message.index("grid")])

		if "queens" in message :

			queens = unstring_queens(message[1+message.index("queens")])

		if "coords" in message :

			coords = unstring_coords(message[1+message.index("coords")])

		if message[0] == "method" :

			eval(message[1+message.index("method")])

		else :

			pass
			# TODO 

			

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

	return rebuilt_queens



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





def main_client(player_ID, sC):

	Checkers = Layout(player_ID, sC)
	print Checkers.player_ID

	# inspection = inspect.getmembers(Checkers, predicate=inspect.ismethod)
	# global methodes
	# methodes=[]
	# for met in inspection:
	# 	methodes.append(met[0])

	#print methodes
	Checkers.run()





######################################################################
######################################################################


sC = socket(AF_INET,SOCK_STREAM)
sC.connect(("127.0.0.1",4242))


opponent_found = False

while opponent_found == False :
	data = sC.recv(4096)
	print data
	if "player" in data :
		opponent_found = True
		sC.sendall('ok')


player_ID=data
main_client(player_ID, sC)