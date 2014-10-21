# [START imports]
import os
import urllib
import string
import random

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
# [END imports]

DEFAULT_GUESTBOOK_NAME = 'default_guestbook'

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

def assignment_key():
    """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
    return ndb.Key('Assignment', 'Assignment')
class Assignment(ndb.Model):
	"""Models an individual Guestbook entry with author, content, and date."""
	id = ndb.StringProperty(indexed=True)
	author = ndb.UserProperty()
	title = ndb.StringProperty(indexed=False)
	content = ndb.StringProperty(indexed=False)
	date = ndb.DateTimeProperty(auto_now_add=True)
class Submission(ndb.Model):
	"""Models an individual Guestbook entry with author, content, and date."""
	author = ndb.StringProperty(indexed=False)
	content = ndb.StringProperty(indexed=False)
	date = ndb.DateTimeProperty(auto_now_add=True)

# [START main_page]
class MainPage(webapp2.RequestHandler):

    def get(self):        

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {            
            'url': url,
            'url_linktext': url_linktext,
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))
# [END main_page]

class TeachersPage(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
		assignments = None
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
			q = Assignment.query(ancestor=assignment_key())
			q = q.filter(Assignment.author==user).order(-Assignment.date)
			assignments = q.fetch(100)
		else:
			url = users.create_login_url(self.request.uri)
			url_linktext = 'Login'

		template_values = {
			'assignments': assignments,
			'user' : user,
			'url': url,
			'url_linktext': url_linktext
		}
		template = JINJA_ENVIRONMENT.get_template('teacher.html')
		self.response.write(template.render(template_values))
		
class AddPage(webapp2.RequestHandler):
	def get(self, id):
		user = users.get_current_user()
		template_values = {
			'assignment' : None
		}
		if user:	
			if id:
				assignment = Assignment.query(ancestor=assignment_key()).filter(
					Assignment.id == id).fetch(1)[0]
				if assignment.author != user:
					self.redirect('/error')
				submissions = Submission.query(ancestor=assignment.key).fetch(1000)
				template_values = {		
					'assignment': assignment,
					'submissions': submissions
				}
			template = JINJA_ENVIRONMENT.get_template('add.html')
			self.response.write(template.render(template_values))
			
	def post(self, id):
		if id:
			assignment = Assignment.query(ancestor=assignment_key()).filter(
					Assignment.id == id).fetch(1)[0]
			assignment.title = self.request.get('title')
			assignment.content = self.request.get('content')	
			assignment.put()
		else:
			while not id:
				id = id_generator()
				existing = Assignment.query(
					Assignment.id == id).fetch(1)
				
			
			user = users.get_current_user()
			assignment = Assignment(parent=assignment_key())
			assignment.id = id
			if user:
				assignment.author = user

			assignment.content = self.request.get('content')
			assignment.title = self.request.get('title')
			assignment.put()

		self.redirect('/add/' + id)
class PromptPage(webapp2.RequestHandler):
	def get(self, id):
		assignment = Assignment.query(ancestor=assignment_key()).filter(
				Assignment.id == id).fetch(1)
		if len(assignment) == 0:
			return self.redirect('/student?found=false')
		template_values = {		
			'assignment': assignment[0],
			'name': self.request.get('name')
		}
		template = JINJA_ENVIRONMENT.get_template('prompt.html')
		self.response.write(template.render(template_values))
			
	def post(self, id):
		assignment = Assignment.query(ancestor=assignment_key()).filter(
			Assignment.id == id).fetch(1)[0]
		content = self.request.get('content')
		submission = Submission(parent=assignment.key)			
		submission.content =  self.request.get('content')
		submission.author =  self.request.get('name')
		submission.put()
		self.redirect('/complete')
		
class StudentPage(webapp2.RequestHandler):
	def get(self):
		template_values = {		
			'found': self.request.get('found')
		}
		template = JINJA_ENVIRONMENT.get_template('student.html')
		self.response.write(template.render(template_values))			
	def post(self):
		code = self.request.get('code')
		self.redirect('/prompt/' + code + '/')
class CompletePage(webapp2.RequestHandler):
	def get(self):
		template = JINJA_ENVIRONMENT.get_template('complete.html')
		self.response.write(template.render())			

class ErrorPage(webapp2.RequestHandler):
	def get(self):
		template = JINJA_ENVIRONMENT.get_template('error.html')
		self.response.write(template.render())	


application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/teacher', TeachersPage),
    ('/student', StudentPage),
    ('/complete', CompletePage),
    ('/error', ErrorPage),
    ('/add/(.*)', AddPage),
    ('/prompt/(.*)/', PromptPage),
], debug=True)
