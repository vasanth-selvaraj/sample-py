from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.types import ARRAY

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'mdxusers'
    __table_args__ = {'schema': 'mercury'}
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.String(50), unique=True, nullable=False)
    firstname = db.Column(db.String(50), nullable=False)
    lastname = db.Column(db.String(50), nullable=False)
    fullname = db.Column(db.String(100))  # Assuming fullname is a concatenation of firstname and lastname
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default="User")  # Default role
    feature = db.Column(ARRAY(db.String), default=[])  # Array of features
    tools = db.Column(ARRAY(db.String), default=[])  # Array of tools
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now(), nullable=False)
    last_login = db.Column(db.DateTime(timezone=True))

    def __repr__(self):
        return f'<User {self.username}>'

