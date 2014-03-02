from coinpage import db

ROLE_USER = 0
ROLE_ADMIN = 1

class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(64), index = True, unique = False)
    email = db.Column(db.String(120), index = True, unique = True)
    location = db.Column(db.String(120), index = True, unique = True)
    adresses = db.relationship('Address', backref='owner', lazy='dynamic')

    def __repr__(self):
        return '<User %r>' % (self.name)

class Address(db.Model):
    __tablename__ = "address"
    id = db.Column(db.Integer, primary_key = True)
    primary = db.Column(db.Boolean, unique=False, default=False)
    address = db.Column(db.String(32), index = True, unique = False)
    coin = db.Column(db.String(10), index = True, unique = False)
