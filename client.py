# -*- coding: utf-8 -*

from Tkinter import*
import time
import os
from socket import *

#import serveur #SCCD9



class Layout:

	def __init__(self):

		self.fenetre = Tk()
		self.fenetre.title("Super Crazy Checkers Deluxe 9000 (v0.7)")
		self.fenetre.geometry("900x600")


		self.click = False

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


		# auto-rotation checkbox
		self.autorot = IntVar()
		self.autorot.set(0)
		check_autorot = Checkbutton(controls,text="Auto-rotate",variable=self.autorot,height=15)

		controls.add(check_autorot)


		# reset button (hopefully will after be included in a menu)
		reset_button = Button(controls,text="Restart",command=self.reset)

		controls.add(reset_button)


		world.add(self.playzone)
		world.add(controls)
		world.pack()


		# event listener for left clicks on board
		self.playzone.bind("<Button-1>", self.left_click)


		# drawing the board for the first time
		self.draw_grid_2(self.game.grid)



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




	# method called by a left click on board
	def left_click(self, event) :

		self.click = True

		# getting where the click has happened
		if self.autorot.get() == 1 :
			if self.game.player == 2 :
				x = event.x / (self.plz_h/self.length)
				y = event.y / (self.plz_w/self.length)

			else :
				x = 9 - event.x/(self.plz_h/self.length)
				y = 9 - event.y/(self.plz_w/self.length)
		else :
			x = event.x / (self.plz_h/self.length)
			y = event.y / (self.plz_w/self.length)


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








	def reset (self) :

		self.fenetre.destroy()
		os.system("python SCCD9_interface.py")



	# (Tkinter's mainloop)
	def loop (self) :
		#afficher à ton tour de jouer
		#self.fenetre.mainloop()
		self.click = False
		while not self.click:
			self.fenetre.update_idletasks()
			self.fenetre.update()




def main_client():
	Checkers = Layout()
	Checkers.loop()



