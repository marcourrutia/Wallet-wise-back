from flask import Flask, jsonify, request
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from flask_bcrypt import Bcrypt
from models import db, User, Type_of_movement, Transaction, Movement_goal, Movement, Goal, Account, Category
from utils import is_valid_email, is_valid_password, find_user_by_email, hash_password, check_password
from flask_cors import CORS
import jwt
from functools import wraps
import os
from datetime import timedelta, datetime
from sqlalchemy import func
from unidecode import unidecode
from flask_mail import Mail, Message
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
JWTManager(app)
bcrypt = Bcrypt(app)
db.init_app(app)
Migrate(app, db)
CORS(app)

OPENAI_API_KEY = os.getenv("OPENAI_TOKEN")

#configuración de mail
app.config["MAIL_SERVER"] = 'smtp.gmail.com'
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "walletwise02@gmail.com"
app.config["MAIL_PASSWORD"] = "potl dfde zjcp ugvs"
mail= Mail(app)



@app.route("/user", methods=["POST"])
def user():
    data = request.get_json()

    first_name = data.get("first_name")
    last_name = data.get("last_name")
    email = data.get("email")
    password = data.get("password")

    if not email or not is_valid_email(email):
        return jsonify({"msg": "Invalid email format"}), 400

    if find_user_by_email(email):
        return jsonify({"msg": "This email address is already registered"}), 409

    if not password or not is_valid_password(password):
        return jsonify({"msg": "Invalid password format"}), 400

    user = User()
    user.email = email
    user.password = hash_password(password, bcrypt)
    user.first_name = first_name
    user.last_name = last_name

    db.session.add(user)
    db.session.commit()

    additional_claims = {"user_id": user.id}
    access_token = create_access_token(identity=data["email"], additional_claims=additional_claims)

    return jsonify({
        "msg": "Success",
            "access_token": access_token,
            "user_id": user.id,
            "user_first_name": user.first_name,
            "user_last_name": user.last_name
    }), 201


@app.route("/login_google", methods=["POST"])
def login_google():
    #comprobar que la información del front llegue al backend
    data = request.get_json()
    expires = timedelta(days=3)
    user = User.query.filter_by(email=data["email"]).first()

    if user is not None:
        additional_claims = {"user_id": user.id}
        access_token = create_access_token(identity=data["email"], additional_claims=additional_claims, expires_delta=expires)

        return jsonify({
            "msg":"Success",
            "access_token": access_token,
        }), 200
    else:
        user = User()

        user.first_name = data["first_name"]
        user.last_name = data["last_name"]
        user.email = data["email"]

        db.session.add(user)
        db.session.commit()

        additional_claims = {"user_id": user.id}
        access_token = create_access_token(identity=data["email"], additional_claims=additional_claims, expires_delta=expires)
        print(access_token)
        return jsonify({
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "email": data["email"],
            "access_token": access_token,
        }), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    expires = timedelta(days=3)

    if not email or not is_valid_email(email):
        return jsonify({"msg": "Invalid email format"}), 400

    user = find_user_by_email(email)
    if user and check_password(user.password, password, bcrypt):
        additional_claims = {"user_id": user.id}
        access_token = create_access_token(identity=data["email"], additional_claims=additional_claims, expires_delta=expires)

        return jsonify({
            "msg": "Success",
            "access_token": access_token,
            "user_id": user.id,
            "user_first_name": user.first_name,
            "user_last_name": user.last_name
        }), 200
    return jsonify({"msg": "Invalid username or password"}), 401

@app.route("/users", methods=["GET"]) #Read
@jwt_required()
def get_users():
    users = User.query.all()
    users = list(map(lambda user: user.serialize(), users))

    return jsonify(users)

@app.route("/user/<int:user_id>", methods=["PUT", "DELETE"])
def update_user(user_id):
        user = User.query.get(user_id)

        if user is None:
            return jsonify("User not found"), 404

        if request.method == "PUT": #Update
            data = request.get_json()

            if data.get("email"):
               return jsonify("The email can't be updated"), 400

            if data.get("first_name"):
                user.first_name = data["first_name"]

            if data.get("last_name"):
                user.last_name = data["last_name"]

            if data.get("password"):
                user.password = data["password"]

            db.session.commit()
            return jsonify(user.serialize()), 200

        if request.method == "DELETE":  # Delete
            db.session.delete(user)
            db.session.commit()
            return jsonify(f"User {user_id} deleted"), 200

@app.route("/account", methods=["GET", "POST"])
@jwt_required()
def account():
    claims = get_jwt()
    user_id = claims.get("user_id")

    if not user_id:
        return jsonify({"msg": "Invalid token"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 403

    if request.method == "GET":
        accounts = Account.query.filter_by(user_id=user_id).all()
        accounts = list(map(lambda account: account.serialize(), accounts))
        return jsonify(accounts), 200

    if request.method == "POST":
        data = request.get_json()
        account = Account()
        account.name = data["name"]
        account.user_id = user_id
        account.state = True

        db.session.add(account)
        db.session.commit()
        return jsonify(
            {"Msg": "Account created successfully"}
        ), 201

@app.route("/account/<int:account_id>", methods=["DELETE"])
@jwt_required()
def delete_account(account_id):
    claims = get_jwt()
    user_id = claims.get("user_id")

    account = Account.query.filter_by(id=account_id, user_id=user_id).first()
    if account:
        db.session.delete(account)
        db.session.commit()
        return jsonify({"msg": "Account deleted"}), 200
    else:
        return jsonify({"msg": "Account not found"}), 404

@app.route("/account/state/<int:account_id>", methods=["PUT"])
@jwt_required()
def update_state_flow(account_id):
    account = Account.query.filter_by(id=account_id).first()
    if account is None:
        return jsonify({"error": "Account not found"}), 404

    account.state = not account.state
    db.session.commit()
    return jsonify(account.serialize()), 200

 #aqui comienza
@app.route("/type_of_movements", methods=["GET"]) #Read
def get_type_of_movements():
    type_of_movements = Type_of_movement.query.all()
    print(type_of_movements[0].serialize())
    type_of_movements = list (map(lambda type_of_movement: type_of_movement.serialize(), type_of_movements))
    return jsonify(type_of_movements)

@app.route("/type_of_movement", methods=["POST"])#Create
def type_of_movement():
        data = request.get_json()

        if isinstance(data, list):
            if len(data) == 0:
                return jsonify({"error": "No se proporcionaron datos"}), 400
            data = data[0]

        if "name" not in data:
            return jsonify({"error": "El campo 'name' es requerido"}), 400

        type_of_movement = Type_of_movement()
        type_of_movement.name = data["name"]

        db.session.add(type_of_movement)
        db.session.commit()

        return jsonify({"msg": "Tipo de movimiento creado"}), 201

@app.route("/type_of_movement/<int:type_of_movements_id>", methods=["PUT", "DELETE"])
def update_type_of_movement(type_of_movements_id):
        return jsonify({"msg": "Transacción creada"}), 201

@app.route("/categorys", methods=["GET"])#Read
def get_category():
    category = Category.query.all()
    category = list(map(lambda category:category.serialize(), category))
    return jsonify(category)

@app.route("/category/<int:category_id>", methods=["PUT", "DELETE"])
def update_category(category_id):
        category = Category.query.get(category_id)

        if category is None:
            return jsonify("category not found"), 404

        if request.method == "PUT": #Update
            data = request.get_json()

            if data.get("name"):
                category.name = data["name"]

            if data.get("type_of_movement_id"):
                category.type_of_movement_id = data["type_of_movement_id"]

            db.session.commit()
            return jsonify(category.serialize()), 200

        if request.method == "DELETE":  # Delete
            db.session.delete(category)
            db.session.commit()
            return jsonify(f"Category {category_id} deleted"), 200
#transacciones
@app.route("/category", methods=["POST"])#Create
def category():

        data = request.get_json()

        if not data:
            return jsonify({"error": "No se proporcionaron datos"}), 400

        category = Category()

        if "name" not in data or "type_of_movement_id" not in data:
            return jsonify({"error": "Faltan campos requeridos (name o type_of_movement_id)"}), 400

        category.name = data["name"]
        category.type_of_movement_id = data["type_of_movement_id"]

        db.session.add(category)
        db.session.commit()

        return jsonify({"msg": "Transacción creada"}), 201

@app.route("/transactions", methods=["GET"])#Read
def get_transaction():
    transaction = Transaction.query.all()
    transaction = list(map(lambda transaction:transaction.serialize(), transaction))
    return jsonify(transaction)

@app.route("/transaction", methods=["POST"])#Create
def transaction():
        data = request.get_json()

        if not data:
            return jsonify({"error": "No se proporcionaron datos"}), 400

        transaction = Transaction()

        if "name" not in data or "category_id" not in data:
            return jsonify({"error": "Faltan campos requeridos (name o category_id)"}), 400

        normalized_name = unidecode(data["name"]).lower()
        existing_transaction = Transaction.query.filter(
            func.lower(Transaction.name) == normalized_name
        ).first()

        if existing_transaction:
            return jsonify({"error": "Transaction with this name already exists."}), 400

        transaction = Transaction(
            name=data["name"],
            category_id=data["category_id"]
        )

        db.session.add(transaction)
        db.session.commit()

        return jsonify({"msg": "Transacción creada"}), 201

@app.route("/transaction/<int:transaction_id>", methods=["PUT", "DELETE"])
@jwt_required()
def update_transaction(transaction_id):
        transaction = Transaction.query.get(transaction_id)

        if transaction is None:
            return jsonify("Transaction not found"), 404

        if request.method == "PUT": #Update
            data = request.get_json()

            if data.get("name"):
                transaction.name = data["name"]

            if data.get("category_id"):
                transaction.category_id = data["category_id"]

            db.session.commit()
            return jsonify(transaction.serialize()), 200

        if request.method == "DELETE":  #Delete
            db.session.delete(transaction)
            db.session.commit()
            return jsonify(f"transaction {transaction_id} deleted"), 200


@app.route('/add-movement', methods=['POST'])
@jwt_required()
def add_movement():
    try:
        user_id = get_jwt_identity()
       
        data = request.get_json()
        amount = data.get('amount')
        transaction_date = data.get('transaction_date')
        account_id = data.get('account_id')
        transaction_id = data.get('transaction_id')


        if not all([amount, transaction_date, account_id, transaction_id]):
            return jsonify({"error": "Missing required fields"}), 400

        transaction_date = datetime.strptime(transaction_date, '%Y-%m-%d')
        transaction = Transaction.query.get(transaction_id)

        goal_name = transaction.name
        recipient_email = user_id
        
        new_movement = Movement(
            amount=amount,
            transaction_date=transaction_date,
            account_id=account_id,
            transaction_id=transaction_id,
            created_at=datetime.now()
        )

        db.session.add(new_movement)
        db.session.commit()

        if transaction.category_id == 2:
            goal = Goal.query.filter(
                Goal.name.ilike(goal_name),
                Goal.account_id == account_id
            ).first()

            if goal:
                new_movement_goal = Movement_goal(
                    movement_id=new_movement.id,
                    goal_id=goal.id,
                )
                db.session.add(new_movement_goal)
                db.session.commit()

                total_contributed = db.session.query(
                    db.func.sum(Movement.amount)
                ).join(Movement_goal, Movement.id == Movement_goal.movement_id) \
                 .filter(Movement_goal.goal_id == goal.id).scalar()

                if total_contributed >= int(goal.fulfillment_amount):
                    send_email_goal_ok(goal.name, recipient_email)

        return jsonify({
            "message": "Movement added successfully",
            "movement": new_movement.serialize()
        }), 201

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/movement/<int:account_id>", methods=["GET"])
@jwt_required()
def get_movement(account_id):
    movement = Movement.query.filter_by(account_id=account_id).all()

    category = list(map(lambda category:category.serialize(), Category.query.all()))
    movement = list(map(lambda movement:movement.serialize(), movement))
    return jsonify({"movement": movement, "category": category}), 200

@app.route("/goal/<int:account_id>", methods=["POST", "GET"])
@jwt_required()
def goal(account_id):
    data = request.get_json() if request.method == "POST" else None

    account = Account.query.get(account_id)
    if not account:
        return jsonify({"message": "Account ID does not exist"}), 404

    if request.method == "GET":
        goals = Goal.query.filter_by(account_id=account_id).all()

        if not goals:
            return jsonify([]), 200

        goals = list(map(lambda goal: goal.serialize(), goals))
        return jsonify(goals), 200

    if request.method == "POST":
        normalized_name = unidecode(data["name"]).lower()

        existing_goal = Goal.query.filter(
            func.lower(Goal.name) == normalized_name,
            Goal.account_id == account_id
        ).first()
        if existing_goal:
            return jsonify({"message": "Goal with this name already exists for this account."}), 400

        goal = Goal(
            name = data["name"],
            fulfillment_amount = data["fulfillment_amount"],
            estimated_monthly = data["estimated_monthly"],
            monthly_contribution = data["monthly_contribution"],
            account_id = account_id
        )

        db.session.add(goal)
        db.session.commit()

        transaction = Transaction(
            name=f"{goal.name}",
            category_id = 2
        )
        db.session.add(transaction)
        db.session.commit()

        return jsonify({"message": "Movement added successfully"}, 201)

@app.route("/goal-by-account/<int:id>", methods=["DELETE", "PUT"])
@jwt_required()
def goal_action(id):
    goal = Goal.query.filter_by(id=id).first()

    if goal is None:
        return jsonify({"error": "Goal not found"}), 404

    if request.method == "DELETE":
        transaction = Transaction.query.filter_by(name=goal.name).first()

        if transaction:
            db.session.delete(transaction)
            print(f"Transaction {transaction.id} deleted")

        db.session.delete(goal)
        db.session.commit()

        return jsonify(f"Goal {id} deleted"), 200

    if request.method == "PUT":
        data = request.get_json()

        if "account_id" in data:
            return jsonify({"error": "account_id cannot be modified"}), 400

        transaction = Transaction.query.filter_by(name=goal.name).first()

        if transaction:
            if data.get("name"):
                transaction.name = data["name"]

        if data.get("name"):
            goal.name = data["name"]

        if data.get("fulfillment_amount"):
            goal.fulfillment_amount = data["fulfillment_amount"]

        if data.get("estimated_monthly"):
            goal.estimated_monthly = data["estimated_monthly"]

        if data.get("monthly_contribution"):
            goal.monthly_contribution = data["monthly_contribution"]

        if data.get("created_at"):
            try:
                goal.created_at = datetime.strptime(data["created_at"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return jsonify({"error": "Invalid date format. Use 'YYYY-MM-DD HH:MM:SS'"}), 400


        db.session.commit()
        return jsonify(goal.serialize()), 200

@app.route("/total-contributed/<int:account_id>", methods=["GET"])
@jwt_required()
def total_contributed(account_id):
    try:
        goals = Goal.query.filter_by(account_id=account_id).all()
        new_goal = []
        current_date = datetime.now()

        for goal in goals:
            movement_goal = Movement_goal.query.filter_by(goal_id=goal.id).all()
            movement_ids = [mgw.movement_id for mgw in movement_goal]

            total_contributed = db.session.query(
                db.func.sum(Movement.amount)
            ).filter(Movement.id.in_(movement_ids)).scalar()

            if goal.created_at:
                months_passed = (current_date.year - goal.created_at.year) * 12 + (current_date.month - goal.created_at.month)

                if goal.estimated_monthly is not None:
                    remaining_time = max(int(goal.estimated_monthly) - months_passed, 0)
                else:
                    remaining_time = 0
            else:
                remaining_time = 0

            monthly_contribution = int(goal.monthly_contribution) if goal.monthly_contribution else 0
            estimated_contribution = months_passed * monthly_contribution

            new_goal.append({
                **goal.serialize(),
                "total_contributed": total_contributed or 0,
                "remaining_time": remaining_time,
                "estimated_contribution": estimated_contribution
            })


        return jsonify(new_goal), 200

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/send_email_goal_ok", methods=["POST"])
@jwt_required()
def send_email_goal_ok(goal_name, recipient_email):
    msg = Message(
        'Hello Walletwise',
        sender='walletwise02@gmail.com',
        recipients=[recipient_email]
    )
    msg.body = f"Congratulations, you have reached your goal. '{goal_name}'"
    mail.send(msg)

    return "Email sent", 200

@app.route("/chatgpt", methods=["POST"])
def send_prompt():
    try:
        data = request.json
        instruction = data.get("instruction")
        prompt = data.get("prompt")
        
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": instruction},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 200,
        }
        
        response = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
        response_data = response.json()

        return jsonify({"response": response_data["choices"][0]["message"]["content"]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

if __name__ == "__main__":
    app.run(host="localhost", port=5050, debug=True)