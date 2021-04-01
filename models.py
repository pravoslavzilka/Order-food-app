from sqlalchemy import Column, Integer, String
from database import Base
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    email = Column(String(120), unique=True)
    password = Column(String(128))
    participants = Column(String(520), default="")
    restaurants = Column(String(520), default="")
    time = Column(String(10), default="")
    date = Column(String(15), default=datetime.now)

    def __init__(self, name=None, email=None):
        self.name = name
        self.email = email

    def __repr__(self):
        return self.name

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id


class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    orders = Column(String(520), default="")
    restaurant = Column(String(1020), default="")
    time = Column(String(10), default="")

    def __init__(self, name=None, email=None):
        self.name = name

    def __repr__(self):
        return self.name



