from flask import Blueprint, request, jsonify
from datetime import datetime
from app.extensions import db
from app.models import LostItem, User

item_bp = Blueprint('item', __name__, url_prefix='/api/item')


@item_bp.route('/publish', methods=['POST'])
def publish_item():
    data = request.get_json()

    # 1️⃣ 参数获取
    user_id = data.get('user_id')
    item_name = data.get('item_name')
    category = data.get('category')
    item_type = data.get('item_type')   # 丢失 / 拾获
    location = data.get('location')
    event_time = data.get('event_time') # 前端传字符串
    description = data.get('description')
    image_path = data.get('image_path')

    # 2️⃣ 必填项校验
    if not all([user_id, item_name, category, item_type, location, event_time]):
        return jsonify({
            "message": "缺少必要参数"
        }), 400

    # 3️⃣ 校验用户是否存在
    user = User.query.get(user_id)
    if not user:
        return jsonify({
            "message": "用户不存在"
        }), 404

    # 4️⃣ 解析时间（字符串 → datetime）
    try:
        event_time = datetime.strptime(event_time, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return jsonify({
            "message": "时间格式错误，应为 YYYY-MM-DD HH:MM:SS"
        }), 400

    # 5️⃣ 创建失物信息对象
    new_item = LostItem(
        item_name=item_name,
        category=category,
        item_type=item_type,
        location=location,
        event_time=event_time,
        description=description,
        image_path=image_path,
        status="待审核",
        user_id=user_id
    )

    # 6️⃣ 写入数据库
    db.session.add(new_item)
    db.session.commit()

    # 7️⃣ 返回结果
    return jsonify({
        "message": "信息发布成功，等待管理员审核",
        "item_id": new_item.item_id
    }), 201


@item_bp.route('/list', methods=['GET'])
def list_items():
    # 1️⃣ 可选查询参数
    category = request.args.get('category')
    item_type = request.args.get('item_type')

    # 2️⃣ 基础查询：只查已发布
    query = LostItem.query.filter_by(status='已发布')

    # 3️⃣ 条件过滤（如果有传参数）
    if category:
        query = query.filter_by(category=category)

    if item_type:
        query = query.filter_by(item_type=item_type)

    # 4️⃣ 查询数据库
    items = query.order_by(LostItem.publish_time.desc()).all()

    # 5️⃣ 组织返回数据
    result = []
    for item in items:
        result.append({
            "item_id": item.item_id,
            "item_name": item.item_name,
            "category": item.category,
            "item_type": item.item_type,
            "location": item.location,
            "event_time": item.event_time.strftime("%Y-%m-%d %H:%M:%S"),
            "description": item.description,
            "publish_time": item.publish_time.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": item.user_id
        })

    return jsonify(result), 200