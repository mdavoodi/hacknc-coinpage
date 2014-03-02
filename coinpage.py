from flask import Flask, request, session, url_for, redirect, \
     render_template, flash, jsonify, g

from flask_oauth import OAuth
from flask.ext.sqlalchemy import SQLAlchemy
import flask.ext.whooshalchemy as whooshalchemy

from wtforms import Form, TextField
from wtforms.validators import Required

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
    __searchable__ = ['full_name']
    id = db.Column(db.Integer, primary_key = True)
    full_name = db.Column(db.String(64), index = True, unique = False)
    username = db.Column(db.String(64), index = True, unique = True)
    email = db.Column(db.String(120), index = True, unique = True)
    location = db.Column(db.String(120), index = True, unique = False)
    adresses = db.relationship('Address', backref='owner', lazy='dynamic')
   
    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'full_name'         : self.full_name,
           'email': self.email,
           'location':self.location,
           # This is an example how to deal with Many2Many relations
           'addresses'  : self.serialize_many2many
       }

    @property
    def serialize_many2many(self):
       """
       Return object's relations in easily serializeable format.
       NB! Calls many2many's serialize property.
       """
       return [ item.serialize for item in self.adresses]

    def __repr__(self):
        return '<User %r>' % (self.full_name)

class Address(db.Model):
    __tablename__ = "address"
    id = db.Column(db.Integer, primary_key = True)
    primary = db.Column(db.Boolean, unique=False, default=False)
    address = db.Column(db.String(32), index = True, unique = False)
    coin = db.Column(db.String(10), index = True, unique = False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'address'         : self.address,
           'coin': self.coin,
       }

whooshalchemy.whoosh_index(app, User)


@app.route('/')
def index():
    logged_in = session.get('logged_in') == True
    return render_template('index.html', logged_in=logged_in, results=[])


@app.route('/register', methods=['GET', 'POST'])
def register():

    """Registers the user."""
    return render_template('register.html')

@app.route('/fb', methods=['GET', 'POST'])
def fb():
    """Testing FB framework."""
    return render_template('fb.html')


def pop_login_session():
    session.pop('logged_in', None)
    session.pop('oauth_token', None)
    session.pop('email', None)

@app.route('/_add_address', methods=['GET', 'POST'])
def add_address():
    currency = request.form['currency']
    address = request.form['address']
    u = User.query.filter_by(email=session['email']).first()
    entry = Address(coin=currency, address=address, owner=u)
    db.session.add(entry)
    db.session.commit()
    return jsonify(result=entry.coin)

@app.route('/search', methods=['GET', 'POST'])
def search():
    query = request.form['searchbox']
    results = User.query.whoosh_search(query).all()
    logged_in = session.get('logged_in') == True
    return render_template('index.html', logged_in=logged_in, results=results)

@app.route('/login')
def login():
    logged_in = session.get('logged_in') == True
    if logged_in:
        user = User.query.filter_by(email=session['email']).first()
        pic_url = "http://graph.facebook.com/%s/picture?height=200" % session['id']
        addr = user.adresses
        return render_template('register.html', user=user, pic_url=pic_url, logged_in=logged_in, adresses=addr)
    return facebook.authorize(callback=url_for('facebook_authorized',
        next=request.args.get('next') or request.referrer or None,
        _external=True))

@app.route("/logout")
def logout():
    pop_login_session()
    return redirect(url_for('index'))

@app.route('/login/authorized')
@facebook.authorized_handler
def facebook_authorized(resp):
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    session['oauth_token'] = (resp['access_token'], '')
    session['logged_in'] = True
    me = facebook.get('/me')
    email = me.data['email']
    user = None
    pic_url = None
    session['email'] = me.data['email']
    session['id'] = me.data['id']
    if user_email_exists(email):
        user = User.query.filter_by(email=me.data['email']).first()
    else:
        user = User(full_name=me.data['name'], email=me.data['email'], location=me.data['location']['name'], username=me.data['id'])

        db.session.add(user)
        db.session.commit()
    pic_url = "http://graph.facebook.com/%s/picture?height=200" % me.data['id']
    return redirect(url_for('login'))

@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')

def user_email_exists(email):
    return not (User.query.filter_by(email=email).first() == None)

if __name__ == '__main__':
    app.debug = True
    app.run()
