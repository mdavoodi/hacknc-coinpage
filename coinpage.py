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

db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key = True)
    full_name = db.Column(db.String(64), index = True, unique = False)
    email = db.Column(db.String(120), index = True, unique = True)
    location = db.Column(db.String(120), index = True, unique = False)
    adresses = db.relationship('Address', backref='owner', lazy='dynamic')

    def __repr__(self):
        return '<User %r>' % (self.full_name)

class Address(db.Model):
    __tablename__ = "address"
    id = db.Column(db.Integer, primary_key = True)
    primary = db.Column(db.Boolean, unique=False, default=False)
    address = db.Column(db.String(32), index = True, unique = True)
    coin = db.Column(db.String(10), index = True, unique = False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


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
    user = None
    pic_url = None
    if user_email_exists(email):
        user = User.query.filter_by(email=me.data['email']).first()
    else:
        user = User(full_name=me.data['name'], email=me.data['email'], location=me.data['location']['name'])

        db.session.add(user)
        db.session.commit()
    pic_url = "http://graph.facebook.com/%s/picture?height=200" % me.data['id']
    return render_template('register.html', user=user, pic_url=pic_url)

@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')

def user_email_exists(email):
    return not (User.query.filter_by(email=email).first() == None)

if __name__ == '__main__':
    app.debug = True
    app.run()
