import json
import sys

class jsonDB:
	def __init__(self,file_db):
		self.file_db = file_db
		try:
			with open(file_db, 'r') as f:
				self.db = json.load(f)
		except:
			self.db = {}

	def select(self,key):
		try:
			return self.db[key]
		except:
			return ''
	def update(self,key,value):
		self.db[key] = value
		with open(self.file_db, 'w') as f:
			json.dump(self.db,f)
