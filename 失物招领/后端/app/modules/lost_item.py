from flask import Blueprint, request, jsonify
from datetime import datetime
from app.extensions import db
from app.models import LostItem, User, ClaimRequest
from functools import wraps
import jwt
from app.config import Config
from werkzeug.utils import secure_filename
import os

item_bp = Blueprint('item', __name__, url_prefix='/api/item')

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print("DEBUG: Token required called", flush=True)
        token = request.headers.get('Authorization')
        print(f"DEBUG: Token header: {token}", flush=True)
        if not token:
            print("DEBUG: No token", flush=True)
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

@item_bp.route('/publish', methods=['POST'])
@token_required
def publish_item():
    print("DEBUG: publish_item called", flush=True)
    user_id = request.user_id

    # 1️⃣ 参数获取
    item_name = request.form.get('item_name')
    category = request.form.get('category')
    item_type = request.form.get('item_type')
    location = request.form.get('location')
    event_time = request.form.get('event_time')
    description = request.form.get('description')

    print(f"Publish attempt: user_id={user_id}, item_name={item_name}, category={category}, item_type={item_type}")

    # 2️⃣ 参数校验
    if not all([item_name, category, item_type, location, event_time, description]):
        return jsonify({"message": "所有字段都是必填的"}), 400

    # 3️⃣ 转换时间
    try:
        event_time = datetime.strptime(event_time, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return jsonify({"message": "事件时间格式错误"}), 400

    # 4️⃣ 处理图片上传
    image_path = ''
    image = request.files.get('image')
    if image:
        filename = secure_filename(image.filename)
        upload_folder = os.path.join(os.getcwd(), 'uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        image.save(os.path.join(upload_folder, filename))
        image_path = filename

    # 5️⃣ 创建物品对象
    new_item = LostItem(
        user_id=user_id,
        item_name=item_name,
        category=category,
        item_type=item_type,
        location=location,
        event_time=event_time,
        description=description,
        image_path=image_path
    )

    # 6️⃣ 写入数据库
    db.session.add(new_item)
    db.session.commit()

    print(f"Publish success: item_id={new_item.item_id}")

    # 7️⃣ 返回结果
    return jsonify({
        "message": "发布成功",
        "item_id": new_item.item_id
    }), 201

@item_bp.route('/my', methods=['GET'])
@token_required
def get_my_items():
    user_id = request.user_id
    items = LostItem.query.filter_by(user_id=user_id).all()
    return jsonify([{
        "item_id": item.item_id,
        "item_name": item.item_name,
        "category": item.category,
        "item_type": item.item_type,
        "location": item.location,
        "event_time": item.event_time.strftime("%Y-%m-%d %H:%M:%S"),
        "description": item.description,
        "image_path": item.image_path,
        "status": item.status,
        "publish_time": item.publish_time.strftime("%Y-%m-%d %H:%M:%S") if item.publish_time else "未知"
    } for item in items]), 200

@item_bp.route('/list', methods=['GET'])
def get_items():
    # 获取查询参数
    search = request.args.get('search')
    category = request.args.get('category')
    item_type = request.args.get('item_type')
    status = request.args.get('status')
    time_range = request.args.get('time_range')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 6))

    # 构建查询
    query = LostItem.query.filter(LostItem.status != '已驳回')

    if search:
        query = query.filter(LostItem.item_name.ilike(f'%{search}%') | LostItem.description.ilike(f'%{search}%'))
    if category:
        query = query.filter_by(category=category)
    if item_type:
        query = query.filter_by(item_type=item_type)
    if status:
        if status == 'unclaimed':
            query = query.filter(LostItem.status.in_(['待审核', '已发布']))
        elif status == 'claimed':
            query = query.filter(LostItem.status.in_(['待审核', '已认领']))
    if time_range:
        from datetime import datetime, timedelta
        days = int(time_range)
        start_date = datetime.now() - timedelta(days=days)
        query = query.filter(LostItem.event_time >= start_date)

    # 分页
    items = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'items': [{
            'item_id': item.item_id,
            'item_name': item.item_name,
            'category': item.category,
            'item_type': item.item_type,
            'location': item.location,
            'event_time': item.event_time.strftime('%Y-%m-%d %H:%M:%S'),
            'description': item.description,
            'image_path': item.image_path,
            'status': item.status,
            'publish_time': item.publish_time.strftime('%Y-%m-%d %H:%M:%S') if item.publish_time else "未知"
        } for item in items.items],
        'total': items.total,
        'pages': items.pages,
        'current_page': items.page
    }), 200

@item_bp.route('/detail/<int:item_id>', methods=['GET'])
def get_item_detail(item_id):
    item = LostItem.query.get(item_id)
    if not item:
        return jsonify({"message": "物品不存在"}), 404
    try:
        user_id = request.user_id
    except AttributeError:
        user_id = None
    return jsonify({
        "item_id": item.item_id,
        "item_name": item.item_name,
        "category": item.category,
        "item_type": item.item_type,
        "location": item.location,
        "event_time": item.event_time.strftime("%Y-%m-%d %H:%M:%S"),
        "description": item.description,
        "image_path": item.image_path,
        "status": item.status,
        "publish_time": item.publish_time.strftime("%Y-%m-%d %H:%M:%S") if item.publish_time else None,
        "publisher": "匿名用户",
        "is_owner": user_id == item.user_id if user_id else False
    }), 200

@item_bp.route('/claim/<int:item_id>', methods=['POST'])
@token_required
def claim_item(item_id):
    user_id = request.user_id
    item = LostItem.query.get(item_id)
    if not item:
        return jsonify({"message": "物品不存在"}), 404
    if item.user_id == user_id:
        return jsonify({"message": "不能认领自己的物品"}), 400
    if item.status not in ['待审核', '已发布']:
        return jsonify({"message": "物品无法认领"}), 400
    # 检查是否已有 pending 请求
    existing = ClaimRequest.query.filter_by(item_id=item_id, claimant_user_id=user_id, status='pending').first()
    if existing:
        return jsonify({"message": "已提交认领请求"}), 400
    message = request.json.get('message', '') if request.is_json else request.form.get('message', '')
    new_request = ClaimRequest(item_id=item_id, claimant_user_id=user_id, message=message)
    db.session.add(new_request)
    db.session.commit()
    return jsonify({"message": "认领请求已提交"}), 200

@item_bp.route('/claim_requests/<int:item_id>', methods=['GET'])
@token_required
def get_claim_requests(item_id):
    item = LostItem.query.get(item_id)
    if not item or item.user_id != request.user_id:
        return jsonify({"message": "无权限"}), 403
    requests = ClaimRequest.query.filter_by(item_id=item_id).all()
    return jsonify([{
        "claim_id": r.claim_id,
        "claimant_username": r.claimant.username,
        "message": r.message,
        "status": r.status,
        "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S")
    } for r in requests]), 200

@item_bp.route('/approve_claim/<int:claim_id>', methods=['POST'])
@token_required
def approve_claim(claim_id):
    claim = ClaimRequest.query.get(claim_id)
    if not claim:
        return jsonify({"message": "请求不存在"}), 404
    item = claim.item
    if item.user_id != request.user_id:
        return jsonify({"message": "无权限"}), 403
    claim.status = 'approved'
    item.status = '已认领'
    db.session.commit()
    return jsonify({"message": "已同意认领"}), 200

@item_bp.route('/reject_claim/<int:claim_id>', methods=['POST'])
@token_required
def reject_claim(claim_id):
    claim = ClaimRequest.query.get(claim_id)
    if not claim:
        return jsonify({"message": "请求不存在"}), 404
    item = claim.item
    if item.user_id != request.user_id:
        return jsonify({"message": "无权限"}), 403
    claim.status = 'rejected'
    db.session.commit()
    return jsonify({"message": "已拒绝认领"}), 200

@item_bp.route('/user_claim_requests', methods=['GET'])
@token_required
def get_user_claim_requests():
    user_id = request.user_id
    # 获取用户所有物品的pending认领请求
    requests = ClaimRequest.query.filter(
        ClaimRequest.item.has(user_id=user_id),
        ClaimRequest.status == 'pending'
    ).all()
    return jsonify([{
        "claim_id": r.claim_id,
        "item_name": r.item.item_name,
        "claimant_username": r.claimant.username,
        "message": r.message,
        "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S")
    } for r in requests]), 200