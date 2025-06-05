from flask import Blueprint, request
from app.controller.user_controller import UserController

users = Blueprint('users', __name__)

@users.route('/users', methods=['GET'])
def get_users():
    return UserController.get_users()

@users.route('/<user_id>/update', methods=['PATCH'])
def profile(user_id):
    return UserController.update_profile(user_id)