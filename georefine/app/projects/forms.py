from flask.ext.wtf import Form, TextField, FileField, file_required

class CreateProjectForm(Form):
	name = TextField('name')
	project_file = FileField(
			'Uploadorama'
			)
