from flask import jsonify, request
from flask_jwt_extended import jwt_required
from app.response import success
from app.model.user import User

class UserController:
    @staticmethod
    @jwt_required() 
    def get_users():    
        users = User.objects()  # ganti dari User.query.all() ke User.objects()
        user_list = [{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at
        } for user in users]

        return success(user_list, "Users get successfully")
    
    @staticmethod
    @jwt_required()
    def update_profile(user_id):
        data = request.get_json()
        user = User.objects(id=user_id).first()

        if not user:
            return jsonify({'message': 'User not found'}), 404

        username = data.get('username')
        if username:
            user.username = username
        user.updated_at = datetime.datetime.utcnow()
        user.save()

        return jsonify({
            'message': 'Profile updated successfully',
            'data': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        }), 200
