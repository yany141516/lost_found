from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models import User
from werkzeug.security import check_password_hash

user_bp = Blueprint('user', __name__, url_prefix='/api/user')


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
    if not user:
        return jsonify({
            "message": "用户不存在"
        }), 404

    # 3️⃣ 校验密码
    if not check_password_hash(user.password, password):
        return jsonify({
            "message": "密码错误"
        }), 401

    # 4️⃣ 登录成功
    return jsonify({
        "message": "登录成功",
        "user_id": user.user_id,
        "username": user.username,
        "is_admin": user.is_admin
    }), 200