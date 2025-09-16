from flask import Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
user_bp = Blueprint('user', __name__)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

@user_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    new_user = User(username=data['username'], email=data['email'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'id': new_user.id, 'username': new_user.username, 'email': new_user.email}), 201

@user_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{'id': u.id, 'username': u.username, 'email': u.email} for u in users])

@user_bp.route('/profile')
def profile():
    return jsonify(message="User profile endpoint")

# Dummy-Routen, um 404-Fehler bei nicht implementierten Endpunkten zu vermeiden
@user_bp.route('/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_user(user_id):
    return jsonify({"error": "Not implemented"}), 501