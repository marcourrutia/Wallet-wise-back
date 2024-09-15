from flask_sqlalchemy import SQLAlchemy
import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)
    email = db.Column(db.String(200), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now())
    count = db.relationship("Count")

def serialize(self):
        return {
            "id":self.id,
            "first_name":self.first_name,
            "last_name":self.last_name,
            "email":self.email,
            "password":self.password,
            "created_at":self.created_at
        }

class Count(db.Model):
    __tablename__ = "count"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.datetime.now())
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    goal = db.relationship("Goal")
    movement = db.relationship("Movement")

def serialize(self):
        return {
            "id":self.id,
            "name":self.name,
            "created_at":self.created_at,
            "user_id":self.user_id
        }

class Goal(db.Model):
    __tablename__ = "goal"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    fulfillment_amount = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.datetime.now())
    estimated_monthly = db.Column(db.String(200))
    monthly_contribution = db.Column(db.Integer)
    count_id = db.Column(db.Integer, db.ForeignKey("count.id"))
    movement_goal = db.relationship("Movement_goal")

def serialize(self):
        return {
            "id":self.id,
            "name":self.name,
            "fulfillment_amount":self.fulfillment_amount,
            "created_at":self.created_at,
            "estimated_monthly":self.estimated_monthly,
            "monthly_contribution":self.monthly_contribution,
            "count_id":self.count_id
        }

class Movement(db.Model):
    __tablename__ = "movement"
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(200))
    transaccion = db.Column(db.String(200))
    amount = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now())
    count_id = db.Column(db.Integer, db.ForeignKey("count.id"))
    movement_goal = db.relationship("Movement_goal")

def serialize(self):
        return {
            "id":self.id,
            "category":self.category,
            "transaccion":self.transaccion,
            "amount":self.amount,
            "created_at":self.created_at,
            "count_id":self.count_id,
        }

class Movement_goal(db.Model):
    __tablename__ = "movement_goal"
    id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey("goal.id"))
    movement_id = db.Column(db.Integer, db.ForeignKey("movement.id"))
    goal = db.relationship("Goal")
    movement = db.relationship("Movement")


def serialize(self):
        return {
            "id":self.id,
            "goal_id":self.goal_id,
            "movement_id":self.movement_id
        }

class Transaction(db.Model):
    __tablename__ = "transaction"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    movement_id = db.Column(db.Integer, db.ForeignKey("movement.id")) 
    movement = db.relationship("Movement", backref=db.backref('transactions', lazy=True))  

def serialize(self):
        return {
            "id":self.id,
            "name":self.name,
            "category_id":self.category_id,
            "movement_id":self.movement_id
        }

class Category(db.Model):
    __tablename__ = "category"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    type_of_movement_id = db.Column(db.Integer, db.ForeignKey("type_of_movement.id"))
    transaction = db.relationship("Transaction")

def serialize(self):
        return {
            "id":self.id,
            "name":self.name,
            "type_of_movement_id":self.category_id
        }

class Type_of_movement(db.Model):
    __tablename__ = "type_of_movement"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    category = db.relationship("Category")
 
def serialize(self):
        return {
            "id":self.id,
            "name":self.name
        }