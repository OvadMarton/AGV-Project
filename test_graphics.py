from graphics import *
from graph_v4 import *
from server_v5 import *
import time
class graphic:
	def __init__(self, graph, bots):
		self.win=GraphWin("test", 400, 550)
		self.make_circles(graph, self.win)
		self.bot_graphics=self.make_bots(bots, self.win)
		self.old_graphics=[]
		
	def make_circles(self, graph, window):
		# ~ circle_list=[]
		for vertex in graph.vertices:
			temp_point=Point(vertex.x*10, vertex.y*10)
			temp=Circle(temp_point, 15)
			text=Text(temp_point, vertex.v_id)
			temp.draw(window)
			text.draw(window)
	def make_bots(self, bots, window):
		bot_graphics=[]
		size=10
		offset=15
		for bot in bots:
			if bot.pos.heading==180:
				pt1=Point(size*bot.pos.x, size*bot.pos.y+offset)
				pt2=Point(size*bot.pos.x-offset*0.7, size*bot.pos.y-0.7*offset)
				pt3=Point(size*bot.pos.x+offset*0.7, size*bot.pos.y-0.7*offset)
				b=Polygon([pt1, pt2, pt3])
				b.setFill("blue")
				bot_graphics.append(b)
			elif bot.pos.heading==0:
				pt1=Point(size*bot.pos.x, size*bot.pos.y-offset)
				pt2=Point(size*bot.pos.x-offset*0.7, size*bot.pos.y+0.7*offset)
				pt3=Point(size*bot.pos.x+offset*0.7, size*bot.pos.y+0.7*offset)
				b=Polygon([pt1, pt2, pt3])
				b.setFill("blue")
				bot_graphics.append(b)
			elif bot.pos.heading==90:
				pt1=Point(size*bot.pos.x+offset, size*bot.pos.y)
				pt2=Point(size*bot.pos.x-offset*0.7, size*bot.pos.y-0.7*offset)
				pt3=Point(size*bot.pos.x-offset*0.7, size*bot.pos.y+0.7*offset)
				b=Polygon([pt1, pt2, pt3])
				b.setFill("blue")
				bot_graphics.append(b)
			elif bot.pos.heading==270:
				pt1=Point(size*bot.pos.x, size*bot.pos.y+offset)
				pt2=Point(size*bot.pos.x-offset*0.7, size*bot.pos.y-0.7*offset)
				pt3=Point(size*bot.pos.x+offset*0.7, size*bot.pos.y-0.7*offset)
				b=Polygon([pt1, pt2, pt3])
				b.setFill("blue")
				bot_graphics.append(b)
			# ~ b.draw(window)
			# ~ print("b:", b)
			# ~ print("bot_graphics:", bot_graphics)
		return bot_graphics
		
	def undraw_bots(self):
		for bot in self.bot_graphics:
			bot.undraw()
	
		
	def update(self, bots):
		i=0
		size=10
		offset=15
		# ~ bot_graphics=[]
		old=copy.copy(self.bot_graphics)
		if len(self.old_graphics)>0:
			for old_bot in self.old_graphics:
				old_bot.undraw()
			self.old_graphics=[]
		else:
			self.win.update()
		for bot in bots:
			if bot.pos.heading==180:
				pt1=Point(size*bot.pos.x, size*bot.pos.y+offset)
				pt2=Point(size*bot.pos.x-offset*0.7, size*bot.pos.y-0.7*offset)
				pt3=Point(size*bot.pos.x+offset*0.7, size*bot.pos.y-0.7*offset)
				b=Polygon([pt1, pt2, pt3])
				b.setFill("blue")
				self.bot_graphics[i]=b
			elif bot.pos.heading==0:
				pt1=Point(size*bot.pos.x, size*bot.pos.y-offset)
				pt2=Point(size*bot.pos.x-offset*0.7, size*bot.pos.y+0.7*offset)
				pt3=Point(size*bot.pos.x+offset*0.7, size*bot.pos.y+0.7*offset)
				b=Polygon([pt1, pt2, pt3])
				b.setFill("blue")
				self.bot_graphics[i]=b
			elif bot.pos.heading==90:
				pt1=Point(size*bot.pos.x+offset, size*bot.pos.y)
				pt2=Point(size*bot.pos.x-offset*0.7, size*bot.pos.y-0.7*offset)
				pt3=Point(size*bot.pos.x-offset*0.7, size*bot.pos.y+0.7*offset)
				b=Polygon([pt1, pt2, pt3])
				b.setFill("blue")
				self.bot_graphics[i]=b
			elif bot.pos.heading==270:
				pt1=Point(size*bot.pos.x-offset, size*bot.pos.y)
				pt2=Point(size*bot.pos.x+offset*0.7, size*bot.pos.y-0.7*offset)
				pt3=Point(size*bot.pos.x+offset*0.7, size*bot.pos.y+0.7*offset)
				b=Polygon([pt1, pt2, pt3])
				b.setFill("blue")
				self.bot_graphics[i]=b
			i+=1
		for element in self.bot_graphics:
			element.draw(self.win)
		for element in old:
			element.undraw()
		


if __name__=="__main__":
	# ~ pt=Point(250,150)
	# ~ pt.draw(win)
	# ~ cir=Circle(pt, 80)
	# ~ cir.setFill("yellow")
	# ~ cir.draw(win)
	# ~ text=Text(pt,"Hello World!")
	# ~ text.draw(win)

	graph=graph("SFGraphVerticesConfig_2.json")
	win=GraphWin("test", 600, 600)
	
	# ~ make_circles(graph, win)
	# ~ print("graph.blocked_vertices", graph.blocked_vertices)
	bots=[]
	bots.append(bot(0, "localhost", 5, 10, 180))
	bots.append(bot(1, "localhost", 10, 10, 0))
	bots.append(bot(2, "localhost", 15, 10, 90))
	bots.append(bot(3, "localhost", 20, 10, 270))
	picture=graphic(graph, bots)
	# ~ print(bots[0].name)
	# ~ print(bots[0].ip)
	# ~ print(bots[0].pos.x)
	# ~ print(bots[0].pos.y)
	# ~ print(bots[0].pos.w)
	# ~ make_bots(bots, win)
	# ~ print("bots_graphics")
	# ~ for bot in bots_graphics:
		# ~ bot.draw(win)
	
	
	win.getMouse()
	win.close()
