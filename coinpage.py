# -*- coding: utf-8 -*-
"""
    MiniTwit
    ~~~~~~~~

    A microblogging application written with Flask and sqlite3.

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from flask import Flask, request, session, url_for, redirect, \
     render_template, flash

from flask_oauth import OAuth
from flask.ext.sqlalchemy import SQLAlchemy

# create our little application :)
app = Flask(__name__)
app.config.from_object('config')


app.debug = app.config['DEBUG']
app.secret_key = app.config['SECRET_KEY']
oauth = OAuth()

facebook = oauth.remote_app('facebook',
    base_url='https://graph.facebook.com/',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    consumer_key= app.config['FACEBOOK_APP_ID'],
    consumer_secret=app.config['FACEBOOK_APP_SECRET'],
    request_token_params={'scope': 'email,user_location'}
)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registers the user."""
    return render_template('register.html')

@app.route('/fb', methods=['GET', 'POST'])
def fb():
    """Testing FB framework."""
    return render_template('fb.html')


@app.route('/logout')
def logout():
    """Logs the user out."""
    flash('You were logged out')
    session.pop('user_id', None)
    return redirect(url_for('public_timeline'))


@app.route('/login')
def login():
    return facebook.authorize(callback=url_for('facebook_authorized',
        next=request.args.get('next') or request.referrer or None,
        _external=True))


@app.route('/login/authorized')
@facebook.authorized_handler
def facebook_authorized(resp):
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    session['oauth_token'] = (resp['access_token'], '')
    me = facebook.get('/me')
    email = me.data['email']
    if not user_email_exists(email):
        return 'Logged in as id=%s name=%s redirect=%s' % \
            (me.data['id'], me.data['name'], request.args.get('next'))
    else:
        return "User already exists"

@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')

def user_email_exists(email):
    from models import User
    return (not User.query.filter(email=email) == None)

if __name__ == '__main__':
    app.debug = True
    app.run()
