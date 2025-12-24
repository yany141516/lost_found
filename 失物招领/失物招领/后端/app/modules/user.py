from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models import User, ClaimNotification, ClaimRequest, LostItem
from functools import wraps
import jwt
from datetime import datetime, timedelta
from app.config import Config
import re

user_bp = Blueprint('user', __name__, url_prefix='/api/user')

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

@user_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    # 1️⃣ 基本参数校验
    username = data.get('username')
    password = data.get('password')
    contact = data.get('contact')

    if not username or not password or not contact:
        return jsonify({
            "message": "用户名、密码和联系方式不能为空"
        }), 400

    # 1.5️⃣ 联系方式格式校验
    if not re.match(r'^\d{11}$', contact):
        return jsonify({
            "message": "联系方式必须是11位纯数字"
        }), 400

    # 2️⃣ 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({
            "message": "用户名已存在"
        }), 400

    # 3️⃣ 检查联系方式是否已存在
    if User.query.filter_by(contact=contact).first():
        return jsonify({
            "message": "联系方式已被注册"
        }), 400

    # 4️⃣ 密码加密
    hashed_password = generate_password_hash(password)

    # 5️⃣ 创建用户对象
    new_user = User(
        username=username,
        password=hashed_password,
        contact=contact,
        is_admin=False
    )

    # 6️⃣ 写入数据库
    db.session.add(new_user)
    db.session.commit()

    # 7️⃣ 返回结果
    return jsonify({
        "message": "注册成功",
        "user_id": new_user.user_id
    }), 201

@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    # 1️⃣ 参数校验
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({
            "message": "用户名和密码不能为空"
        }), 400

    # 2️⃣ 查询用户
    user = User.query.filter_by(username=username).first()
    print(f"Login attempt: username={username}, user found={user is not None}")
    if not user:
        return jsonify({
            "message": "用户不存在"
        }), 404

    # 3️⃣ 校验密码
    password_match = check_password_hash(user.password, password)
    print(f"Password check: match={password_match}")
    if not password_match:
        return jsonify({
            "message": "密码错误"
        }), 401

    # 4️⃣ 登录成功
    token = jwt.encode({
        'user_id': user.user_id,
        'username': user.username,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, Config.SECRET_KEY, algorithm='HS256')
    return jsonify({
        "message": "登录成功",
        "token": token,
        "user": {
            "user_id": user.user_id,
            "username": user.username,
            "is_admin": user.is_admin
        }
    }), 200

@user_bp.route('/profile', methods=['GET'])
@token_required
def get_profile():
    user_id = request.user_id
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "用户不存在"}), 404

    unread_notif_count = 0
    pending_audit_count = 0
    
    if user.is_admin:
        unread_notif_count = ClaimNotification.query.filter_by(admin_id=user_id, is_read=False).count()
        pending_audit_count = LostItem.query.filter_by(status='待审核').count()

    # Pending claims for items published by this user
    pending_claims_count = ClaimRequest.query.filter(
        ClaimRequest.item.has(user_id=user_id),
        ClaimRequest.status == 'pending'
    ).count()

    return jsonify({
        "user_id": user.user_id,
        "username": user.username,
        "contact": user.contact,
        "is_admin": user.is_admin,
        "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S") if user.created_at else "未知",
        "unread_notif_count": unread_notif_count,
        "pending_audit_count": pending_audit_count,
        "pending_claims_count": pending_claims_count
    }), 200