#!/usr/bin/python3
from flask import Flask, render_template, request, redirect
from flask import jsonify, url_for, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Book

# imports for login functionality
from flask import session as login_session
import random
import string

# importing oauth and other relative resources
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

# Configure application
app = Flask(__name__)

# Google client information
file = json.loads(open('client_secrets.json', 'r').read())
CLIENT_ID = file['web']['client_id']
APPLICATION_NAME = 'Item Catalog'

# Connect to DB and create DB session
engine = create_engine('sqlite:///itemcatalog.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Helper functions

# Check current logged in user


def validateUser():
    email = login_session['email']
    return session.query(User).filter_by(email=email).one_or_none()


# Check admin information


def validateAdmin():
    return session.query(User).filter_by(
        email='leandrikuyk@gmail.com').one_or_none()


def createUser(login_session):
    newUser = User(name=login_session['name'], email=login_session['email'],
                   url=login_session['image'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


# Create a state token in order to prevent request forgery
# Store it in the session for later validation
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase +
                    string.digits) for x in xrange(32))
    login_session['state'] = state
    return state


# Query all books in DB
def allBooks():
    return session.query(Book).all()

# Google Sign in function


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    print('request', request)
    # @todo: THIS IS THE PROBLEM! Make request.args.get('state') == login_session['state']
    if request.args.get('state') == login_session['state']:
        print('Request args do not equal login session')
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data
    try:
        # Upgrade authorization code into credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check access token validity
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # Abort if there was error in access token info
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that access token is used for intended user
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps('Token user id does not match given user id'), 401)
        response.headers['Content-Type'] = 'application/json'
        print('User id does not equal Google plus id')
        return response
    # Verify that access token is valid for this application
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps('Token client id does not match app id'), 401)
        print 'Token client id does not match app id.'
        response.headers['Content-Type'] = 'application/json'
        return response
    # Check to see if user is already logged in
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use
    login_session['credentials'] = access_token
    login_session['id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()

    login_session['name'] = data['name']
    login_session['image'] = data['picture']
    login_session['email'] = data['email']

    # Check if user exists - if not make new one
    if not validateUser():
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['name']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['image']
    output += ' "style="width: 300px; height: 300px; border-radius: 150px;'
    output += '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    print 'Login successful'
    return output


# Revoke a current users token and reset their login session
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session['credentials']
    # Only disconnect a connected user
    print 'In gdisconnect access token is %s', access_token
    print 'Username is: '
    print login_session['name']
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps({'state': 'notConnected'}), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Execute HTTP GET requests to revoke current token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'Result is '
    print result

    if result['status'] == '200':
        # Reset the user's session.
        del login_session['credentials']
        del login_session['id']
        del login_session['name']
        del login_session['email']
        del login_session['image']
        login_session['name'] = 'null'
        response = make_response(json.dumps({'state': 'disconnected'}), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # If given token is invalid
        response = make_response(json.dumps({'state': 'error'}),  401)
        response.headers['Content-Type'] = 'application/json'
        return response

# Logs user out of bookshelf


@app.route('/disconnect', methods=['POST'])
def disconnect():
    # Disconnect based on name of user
    if login_session.get('name') == 'user_id':
        return gdisconnect()
    else:
        response = make_response(json.dumps({'state': 'notConnected'}), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

# JSON API's to view book information


@app.route('/bookshelf/JSON')
def bookshelfJSON():
    books = session.query(Book).all()
    return jsonify(books=[book.serialize for book in books])


@app.route('/bookshelf/categories/<string:categories>/JSON')
def categoryJSON(categories):
    books = session.query(Book).filter_by(categories=categories).all()
    return jsonify(books=[book.serialize for book in books])


@app.route('/bookshelf/categories/<string:categories>/<int:books_id>/JSON')
def booksJSON(categories, books_id):
    books = session.query(Book).filter_by(categories=categories,
                                          id=books_id).first()
    return jsonify(books=book.serialize)

# APP ROUTES

# Homepage


@app.route('/')
@app.route('/bookshelf')
def showBookshelf():
    books = allBooks()
    return render_template('bookshelf.html', books=books,
                           login_session=login_session)


# Add new book to database


@app.route('/bookshelf/add/', methods=['GET', 'POST'])
def addBook():
    if 'name' in login_session and login_session['name'] != 'null':
        # Check if user is logged in
        if request.method == 'POST':
                addBook = Book(name=request.form['name'],
                               author=request.form['author'],
                               cover=request.form['cover'],
                               description=request.form['description'],
                               categories=request.form['categories'],
                               user_id=validateUser().id)
                session.add(addBook)
                session.commit()
                return redirect(url_for('showBookshelf'))
        else:
            return render_template('addbook.html',
                                   title='Add New Book',
                                   message='All Fields Required',
                                   login_session=login_session)
    else:
        state = showLogin()
        books = allBooks()
        return render_template('bookshelf.html', books=books,
                               login_session=login_session,
                               message='Login to Add Book')


# Show the books that are in each category


@app.route('/bookshelf/categories/<string:categories>')
def categorizeBooks(categories):
    books = session.query(Book).filter_by(categories=categories).all()
    state = showLogin()
    return render_template('bookshelf.html', books=books,
                           error='No Books Have Been Added to this Category',
                           state=state, login_session=login_session)


# Show the specific books and their information


@app.route('/bookshelf/categories/<string:categories>/<int:books_id>')
def bookInfo(categories, books_id):
    book = session.query(Book).filter_by(id=books_id,
                                         categories=categories).first()
    state = showLogin()
    if book:
        return render_template('bookinfo.html', book=book, state=state,
                               login_session=login_session)
    else:
        return render_template('bookshelf.html',
                               error='No Book Found with this Category',
                               state=state, login_session=login_session)


# Edit book information


@app.route('/bookshelf/categories/<string:categories>/<int:books_id>/edit/',
           methods=['GET', 'POST'])
def editBook(categories, books_id):
    editedBook = session.query(Book).filter_by(id=books_id,
                                               categories=categories).first()
    if request.method == 'POST':
        # Check if user is logged in
        if 'name' in login_session and login_session['name'] != 'null':
            name = request.form['name']
            author = request.form['author']
            cover = request.form['cover']
            description = request.form['description']
            categories = request.form['categories']
            user_id = validateUser().id
            admin_id = validateAdmin().id
            # Check user is same as book creator
            if editedBook.user_id == user_id or user_id == admin_id:
                if name and author and cover and description and categories:
                    editedBook.name = name
                    editedBook.author = author
                    editedBook.cover = cover
                    description = description.replace('\n', '<br>')
                    editedBook.description = description
                    editedBook.categories = categories
                    session.add(editedBook)
                    session.commit()
                    return redirect(url_for('bookInfo',
                                            categories=editedBook.categories,
                                            books_id=editedBook.id))
                else:
                    return render_template('editbook.html',
                                           title='Edit Book Details',
                                           editedBook=editedBook,
                                           login_session=login_session,
                                           message='All Fields are Required')
            else:
                return render_template('bookinfo.html', editedBook=editedBook,
                                       login_session=login_session,
                                       message='Only Book Creator \
                                               can Edit Book')
        else:
            state = showLogin()
            return render_template('bookinfo.html', editedBook=editedBook,
                                   state=state,
                                   login_session=login_session,
                                   message='Login to Edit Book')
    elif editedBook:
        state = showLogin()
        if 'name' in login_session and login_session['name'] != 'null':
            user_id = validateUser().id
            admin_id = validateAdmin().id
            if user_id == editedBook.user_id or user_id == admin_id:
                return render_template('editbook.html',
                                       title='Edit Book',
                                       editedBook=editedBook, state=state,
                                       login_session=login_session)
            else:
                return render_template('bookinfo.html', editedBook=editedBook,
                                       login_session=login_session,
                                       message='Only Book Creator \
                                               can Edit Book')
        else:
            return render_template('bookinfo.html', editedBook=editedBook,
                                   login_session=login_session,
                                   message='Login to Edit Book')
    else:
        state = showLogin()
        return render_template('bookshelf.html',
                               error='No Book Found with this Category',
                               state=state, login_session=login_session)


# Delete specific book


@app.route('/bookshelf/categories/<string:categories>/<int:books_id>/delete/',
           methods=['GET', 'POST'])
def deleteBook(categories, books_id):
    book = session.query(Book).filter_by(categories=categories,
                                         id=books_id).first()
    state = showLogin()
    if book:
        # Check if user is logged in
        if 'name' in login_session and login_session['name'] != 'null':
            user_id = validateUser().id
            admin_id = validateAdmin().id
            if user_id == book.user_id or user_id == admin_id:
                session.delete(book)
                session.commit()
                return redirect(url_for('showBookshelf'))
            else:
                return render_template('bookinfo.html', book=book,
                                       state=state,
                                       login_session=login_session,
                                       message='Only Creator can Delete Book')
        else:
            return render_template('bookinfo.html', book=book,
                                   state=state,
                                   login_session=login_session,
                                   message='Login to Delete Book')
    else:
        return render_template('bookshelf.html',
                               error='No Book Found in database \
                                      with this category',
                               state=state, login_session=login_session)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='', port=8000)
