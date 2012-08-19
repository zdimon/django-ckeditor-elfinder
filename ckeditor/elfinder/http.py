from ckeditor.elfinder.commands import COMMANDS_MAP

class HttpRequestParser(object):
	def __init__(self, request, get=None, post=None, files=None):
		self._req = request
		self.post = post or {}
		self.get = get or {}
		self.files = files or {}
		self.command = ''
		self.params = {}
		try:
			self.parse()
		except Exception, e:
			print e
		
	def parse(self):
		self.params = dict(self.get)
		self.params.update(self.post)
		try:
			self.params.update(self.files)
		except:
			pass
		self.command = self.params.get('cmd', None)
		if type(self.command) == type([]):
			self.command = self.command[0]
		if self.command in COMMANDS_MAP:
			self.command = COMMANDS_MAP[self.command]
		else:
			self.command = None
	def ok(self):
		if not type(self.command) == type(object):
			return False
		return True
		
		
	