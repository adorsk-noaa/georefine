from georefine.app import db

class Project(db.Model):
	__tablename__ = 'projects_project'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(50), unique=True)
	dir = db.Column(db.String)

	def __init__(self, id=None, name=None, dir=None):
		self.id = id
		self.name = name
		self.dir = dir
