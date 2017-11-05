# keeps track of the last n elements put into here
class LRU(object):
	def __init__(self, n):
		self.arr = [None for i in range(n)]
	
	def push(self, obj):
		self.arr[1:] = self.arr[:-1]
		self.arr[0] = obj
