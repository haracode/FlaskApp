from flask import Flask, render_template, request, url_for, redirect, session, g, flash
from cms import Content
from functools import wraps
from wtforms import Form, BooleanField, TextField, PasswordField, validators
from passlib.hash import sha256_crypt
from MySQLdb import escape_string as thwart
import gc

from connectdb import connection

app = Flask(__name__)

TOPIC_DICT = Content()



@app.route('/')
def homepage():
    return render_template("main.html")

#@app.route('/board/') >this link works as well, two different urls link to the same page
@app.route('/dashboard/')
def dashboard():
    #return ("hi") >test to see if webpage is responding without errors
	return render_template("dashboard.html", TOPIC_DICT = TOPIC_DICT)
	
@app.route('/confirm/')
def confirm():
	return render_template("confirm.html", TOPIC_DICT = TOPIC_DICT)
	
@app.route('/account/')
def account():
	return render_template("account.html", TOPIC_DICT = TOPIC_DICT)

@app.errorhandler(404)
def page_not_found(err):
    #return ("hi") test to see if webpage is responding without errors
	return render_template("404.html")
	
@app.errorhandler(405)
def method_not_found(err):
	return render_template("405.html")
	
def login_required(x):
#x is the function that is being wrapped
	@wraps(x)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return x(*args, **kwargs)
		else:
			flash("You need to login first")
			return redirect(url_for("login_page"))
	return wrap
		
@app.route('/logout/')
@login_required	
def logout():
	session.clear()
	flash("You have been logged out")
	gc.collect
	return redirect(url_for('homepage'))
	

@app.route('/login/', methods=["GET","POST"])
def login_page():
	error = ""
	try:
		c, conn = connection()
		if request.method == "POST":
		
			data = c.execute("SELECT * FROM users WHERE username = %s", thwart(request.form['username']))
			data = c.fetchone()[2]
			
			#if int(data) == 0:
			#	error = "username and password not found. Try again"
			
			#if sha256_crypt.verify(request.form['password'], data):
			if request.form['password']:
				session['logged_in'] = True
				session['username'] = request.form['username']
				
				return redirect(url_for('account'))
				
			else:
				error = "Username and password not found. Try again"
				
		gc.collect()
		
		return render_template("login.html", error = error)
		
	except Exception as e:
		error= "Username and password not found. Try again"
		return render_template("login.html", error = error)
	

class SignUpForm(Form):
	username = TextField('Username', [validators.Length(min=4, max=20)])
	email = TextField('Email Address', [validators.Length(min=6, max=50)])
	password = PasswordField('Password', [validators.Required(), validators.EqualTo('confirm', message="Passwords do not match!")])
	confirm = PasswordField('Repeat Password')
	
	
@app.route('/signup/', methods = ['GET', 'POST'])
def signup_page():
	try:
		form = SignUpForm(request.form)
		
		if request.method == "POST" and form.validate():
			username = form.username.data
			email = form.email.data
			password = sha256_crypt.encrypt((str(form.password.data)))
			c, conn = connection()
			
			x = c.execute("SELECT * FROM users WHERE username = (%s)", (thwart(username)))
			
			if int(x) > 0:
				flash("Username taken")
				return render_template('signup.html', form = form)
			
			else:
				c.execute("INSERT INTO users (username, password, email, tracking) VALUES (%s, %s, %s, %s)", (thwart(username), thwart(password), thwart(email), thwart("/introduction/")))
				conn.commit()
				flash("You signuped successfully!")
				c.close()
				conn.close()
				gc.collect()
				
				session['logged_in'] = True
				session['username'] = username
				#Change the URL for the signup user
				return redirect(url_for('confirm'))
		
		return render_template("signup.html", form=form)
		
	except Exception as err:
		return (str(err))

	
	
#Displaying 500 errors	
#@app.route('/errordisplay/')
#def errordisplay():
#	try:
#		return render_template("dashboard.html", TOPIC_DICT = TOPIC_DICT)
#	except Exception as err:
#		return render_template("500.html", error = err)

if __name__ == "__main__":
    app.run()
