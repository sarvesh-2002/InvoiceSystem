#https://www.geeksforgeeks.org/profile-application-using-python-flask-and-mysql/

# Store this code in 'app.py' file
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import uuid

app = Flask(__name__)


app.secret_key = 'your secret key'


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'darshan'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'invoice_mng_sys'


mysql = MySQL(app)


@app.route("/")
@app.route("/home")
def home():
	return render_template("home.html")

@app.route('/register', methods =['GET', 'POST'])
def register():
	if 'loggedin' in session:
		return render_template('invoices.html')
	msg = ''
	if request.method == 'POST' and 'name' in request.form and 'email' in request.form and 'password' in request.form:
		name = request.form['name']
		email = request.form['email']
		password = request.form['password']
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute('SELECT * FROM user WHERE email = % s', (email, ))
		account = cursor.fetchone()
		if account:
			msg = 'Account already exists !'
		elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
			msg = 'Invalid email address !'
		else:
			cursor.execute('INSERT INTO user VALUES ( %s, % s, % s, % s)', (str(uuid.uuid1())[:8], name, email, password))
			mysql.connection.commit()
			msg = 'You have successfully registered !'
			return render_template('login.html', msg=msg)
	elif request.method == 'POST':
		msg = 'Please fill out the form !'
	return render_template('create-account.html', msg = msg)

@app.route('/login', methods =['GET', 'POST'])
def login():
	if 'loggedin' in session:
		return redirect(url_for('invoices'))
	msg = ''
	if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
		email = request.form['email']
		password = request.form['password']
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute('SELECT * FROM user WHERE email = % s AND password = % s', (email, password, ))
		account = cursor.fetchone()
		if account:
			session['loggedin'] = True
			session['id'] = account['id']
			msg = 'Logged in successfully !'
			return redirect(url_for('invoices'))
		else:
			msg = 'Incorrect username / password !'
	return render_template('login.html', msg = msg)

@app.route("/invoices", methods=['GET', 'POST'])
def invoices():
	fltr = request.args.get('filter')
	new = request.args.get('new')
	
	if 'loggedin' in session:
		if new == '1':
			return render_template('create-invoice.html')
		try:
			if request.method == 'POST':
				email = request.form['email']
				issue_date = request.form['issue-date']
				due_date = request.form['due-date']
				amount = request.form['amount']
				cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
				cursor.execute('SELECT client_id, name FROM client WHERE uid = % s and email= % s', (session['id'], email ))
				data = cursor.fetchone()
				client_id = data['client_id']
				name = data['name']
				cursor.execute('INSERT INTO invoice VALUES ( %s, %s, %s, %s, % s, % s, % s, % s)', (session['id'], str(uuid.uuid1())[:8],client_id, name, issue_date, due_date, amount, 'due'))
				mysql.connection.commit()

		except Exception as e:
			print(e)

		finally:
			cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
			if fltr == 'paid':
				cursor.execute('SELECT invoice_id, client, issue_date, status, amount FROM invoice WHERE uid = % s and status=% s', (session['id'], 'paid'))
			elif fltr == 'due':
				cursor.execute('SELECT invoice_id, client, issue_date, status, amount FROM invoice WHERE uid = % s and status=% s', (session['id'], 'due'))
			else:
				cursor.execute('SELECT invoice_id, client, issue_date, status, amount FROM invoice WHERE uid = % s', (session['id'], ))
			
			data = [i for i in cursor.fetchall()]
			return render_template("invoices.html", data = data)
	return redirect(url_for('login'))

@app.route("/update", methods=['GET', 'POST'])
def update():
	if 'loggedin' in session:
		invoice_id = request.args.get('id')
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		if request.method == 'POST':
			email = request.form['email']
			issue_date = request.form['issue-date']
			due_date = request.form['due-date']
			amount = request.form['amount']
	
			cursor.execute('UPDATE invoice SET issue_date = %s, due_date = %s, amount = %s WHERE invoice_id=%s;', (issue_date, due_date, amount, invoice_id,))
			mysql.connection.commit()
			cursor.execute('SELECT invoice_id, client, issue_date, status, amount FROM invoice WHERE uid = % s', (session['id'], ))
			data = [i for i in cursor.fetchall()]
			#change browser url also when rendering template
			return redirect(url_for('invoices'))
			return render_template("invoices.html", data = data)
		else:
			cursor.execute('select client_id, issue_date, due_date, amount, invoice_id from invoice where invoice_id=%s', (invoice_id,))
			data = cursor.fetchone()
			client_id = data['client_id']
			cursor.execute('select email from client where client_id=%s', (client_id,))
			email = cursor.fetchone()['email']
			data['email'] = email
			return render_template("update-invoice.html", data=data)

	return redirect(url_for('login'))
	
@app.route("/delete", methods=['GET'])
def delete():
	if 'loggedin' in session:
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		invoice_id = request.args.get('id')
		client_id = request.args.get('cid')
		if client_id:
			cursor.execute('DELETE FROM client WHERE client_id=%s;', (client_id,))
			mysql.connection.commit()
			cursor.execute('SELECT name, phone, email from client;')
			account = [i for i in cursor.fetchall()]
			return redirect(url_for('clients'))
			return render_template("clients.html", account = account)
		else:
			
			cursor.execute('DELETE FROM invoice WHERE invoice_id=%s;', (invoice_id,))
			mysql.connection.commit()
			cursor.execute('SELECT invoice_id, client, issue_date, status, amount FROM invoice WHERE uid = % s', (session['id'], ))
			data = [i for i in cursor.fetchall()]
			return redirect(url_for('invoices'))
			return render_template("invoices.html", data = data)

	return redirect(url_for('login'))
	
@app.route("/clients", methods=['GET', 'POST'])
def clients():
	new = request.args.get('new')
	if 'loggedin' in session:
		if new == '1':
			return render_template('create-client.html')
		try:
			if request.method == 'POST':
				name = request.form['name']
				phone = request.form['phone']
				email = request.form['email']
				cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
				cursor.execute('INSERT INTO client VALUES ( %s, %s, % s, % s, % s)', (session['id'], str(uuid.uuid1())[:8], name, phone, email))
				mysql.connection.commit()
		except Exception as e:
			print(e)		
		finally:
			cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
			cursor.execute('SELECT client_id, name, phone, email from client;')
			account = [i for i in cursor.fetchall()]
			return render_template("clients.html", account = account)
	return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    return redirect(url_for('login'))

if __name__ == "__main__":
	app.run(host ="0.0.0.0", port = 5000, debug=True)

