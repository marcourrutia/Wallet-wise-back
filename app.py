from flask import Flask, jsonify, request
from flask_migrate import Migrate
from models import db, User, Type_of_movement, Transaction, Movement_goal, Movement, Goal, Count, Category

app = Flask(__name__) 
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///wallet-wise.db"
db.init_app(app)
Migrate(app, db)

@app.route("/", methods=["GET"])
def home():
    return "<h1>Hola desde Flask PT 50</h1>"

@app.route("/user", methods=["POST"])
def user():
   data = request.get_json()
   user = User()
   user.first_name = data["first_name"]
   user.last_name = data["last_name"]
   user.email = data["email"]
   user.password = data["password"]
   
   db.session.add(user) 
   db.session.commit()
    
   return jsonify ({"msg":"Usuario creado"}), 200

@app.route("/users", methods=["GET"]) #Read
def get_users():
    users = User.query.all()
    users = list(map(lambda user: user.serialize(), users))

    return jsonify(users)

@app.route("/user/<int:user_id>", methods=["PUT", "DELETE"])
def update_user(user_id):
    if request.method == "PUT": #Update
        user = User.query.get(user_id)
        if user is not None:
            data = request.get_json()
            user.name = data["name"]
            if data["password"]:
                return jsonify("No puedes modificar la contraseña"),400

            db.session.commit()
            return jsonify(user.serialize()), 200
        else:
            return jsonify("Usuario no encontrado"), 404
    else:
        user = User.query.get(user_id) #Delete
        if user is not None:
            db.session.delete(user)
            db.session.commit()

            return jsonify("Usuario eliminado"), 201
        else:
            return jsonify("Usuario no encontrado"), 404
        
if __name__ == "__main__":
    app.run(host="localhost", port=5050, debug=True)