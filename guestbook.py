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
# We set a parent key on the 'Greetings' to ensure that they are all in the same
# entity group. Queries across the single entity group will be consistent.
# However, the write rate should be limited to ~1/second.

def guestbook_key(guestbook_name=DEFAULT_GUESTBOOK_NAME):
    """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
    return ndb.Key('Guestbook', guestbook_name)
class Greeting(ndb.Model):
    """Models an individual Guestbook entry with author, content, and date."""
    author = ndb.UserProperty()
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)

class Assignment(ndb.Model):
	"""Models an individual Guestbook entry with author, content, and date."""
	id = ndb.StringProperty(indexed=True)
	author = ndb.UserProperty()
	title = ndb.StringProperty(indexed=False)
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
			assignments_query = Assignment.query(
				Assignment.author==user).order(-Assignment.date)
			assignments = assignments_query.fetch(100)
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
	def get(self):
		user = users.get_current_user()
		if user:				
			template_values = {				
			}
			template = JINJA_ENVIRONMENT.get_template('add.html')
			self.response.write(template.render(template_values))
			
	def post(self):
		
		id = ""
		while not id:
			id = id_generator()
			existing = Assignment.query(
				Assignment.id == id).fetch(1)
			
		
		user = users.get_current_user()
		assignment = Assignment()
		assignment.id = id
		if user:
			assignment.author = user

		assignment.content = self.request.get('content')
		assignment.title = self.request.get('title')
		assignment.put()

		self.redirect('/teacher')
class PromptPage(webapp2.RequestHandler):
	def get(self, id):
		assignment = Assignment.query(
				Assignment.id == id).fetch(1)
		template_values = {		
			'assignment': assignment[0]
		}
		template = JINJA_ENVIRONMENT.get_template('prompt.html')
		self.response.write(template.render(template_values))
			
	def post(self):
		user = users.get_current_user()
		assignment = Assignment()

		if user:
			assignment.author = user

		assignment.content = self.request.get('content')
		assignment.title = self.request.get('title')
		assignment.put()

		self.redirect('/teacher')
		
class StudentPage(webapp2.RequestHandler):
	def get(self):
		template = JINJA_ENVIRONMENT.get_template('student.html')
		self.response.write(template.render())			
	def post(self):
		code = self.request.get('code')
		self.redirect('/prompt/' + code)
		


application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/teacher', TeachersPage),
    ('/student', StudentPage),
    ('/add', AddPage),
    ('/prompt/(.*)', PromptPage),
], debug=True)
