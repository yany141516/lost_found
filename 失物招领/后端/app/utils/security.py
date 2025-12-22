from flask import request, jsonify
from functools import wraps
import jwt
from app.config import Config

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': '缺少token'}), 401
        try:
            token = token.replace('Bearer ', '')
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            request.user_id = payload['user_id']
            request.username = payload['username']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'token已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': '无效token'}), 401
        return f(*args, **kwargs)
    return decorated_function