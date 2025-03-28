from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)
    email = db.Column(db.String(200), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now())
    account = db.relationship("Account")

    def serialize(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "created_at": self.created_at
        }
    
class Account(db.Model):
    __tablename__ = "account"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.now())
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    state = db.Column(db.Boolean, nullable=False)
    goal = db.relationship("Goal")
    movement = db.relationship("Movement")

    def serialize(self):
        return {
            "id":self.id,
            "name":self.name,
            "created_at":self.created_at,
            "user_id":self.user_id,
            "state":self.state
        }

class Goal(db.Model):
    __tablename__ = "goal"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    fulfillment_amount = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.now())
    estimated_monthly = db.Column(db.String(200))
    monthly_contribution = db.Column(db.Integer)
    account_id = db.Column(db.Integer, db.ForeignKey("account.id"))
    movement_goal = db.relationship("Movement_goal")

    def serialize(self):
        return {
            "id":self.id,
            "name":self.name,
            "fulfillment_amount":self.fulfillment_amount,
            "created_at":self.created_at,
            "estimated_monthly":self.estimated_monthly,
            "monthly_contribution":self.monthly_contribution,
            "account_id":self.account_id
        }
    
class Transaction(db.Model):
    __tablename__ = "transaction"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    movements = db.relationship("Movement", back_populates="transaction")  

    def serialize(self):
        return {
            "id":self.id,
            "name":self.name,
            "category_id":self.category_id
        }
    
class Movement(db.Model):
    __tablename__ = "movement"
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer)
    transaction_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.now())
    account_id = db.Column(db.Integer, db.ForeignKey("account.id"))
    transaction_id = db.Column(db.Integer, db.ForeignKey("transaction.id"))
    movement_goal = db.relationship("Movement_goal")
    transaction = db.relationship("Transaction", back_populates="movements")

    def serialize(self):
        return {
            "id":self.id,
            "amount":self.amount,
            "transaction_date":self.transaction_date,
            "created_at":self.created_at,
            "account_id":self.account_id,
            "transaction_id":self.transaction_id,
            "transaction":self.transaction.name,
            "category":self.category()
        }

    def category(self):
        categoria = Category.query.filter_by(id=self.transaction.category_id).first()
        return categoria.name


class Movement_goal(db.Model):
    __tablename__ = "movement_goal"
    id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey("goal.id"))
    movement_id = db.Column(db.Integer, db.ForeignKey("movement.id"))

    def serialize(self):
        return {
            "id":self.id,
            "goal_id":self.goal_id,
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
            "type_of_movement_id":self.type_of_movement_id
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