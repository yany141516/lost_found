from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import User, LostItem, AuditRecord, ClaimNotification

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/audit', methods=['POST'])
def audit_item():
    data = request.get_json()

    # 1️⃣ 获取参数
    admin_id = data.get('admin_id')
    item_id = data.get('item_id')
    result = data.get('result')   # 通过 / 驳回
    reason = data.get('reason')   # 可选

    # 2️⃣ 参数校验
    if not all([admin_id, item_id, result]):
        return jsonify({
            "message": "缺少必要参数"
        }), 400

    if result not in ['通过', '驳回']:
        return jsonify({
            "message": "审核结果必须为“通过”或“驳回”"
        }), 400

    # 3️⃣ 校验管理员身份
    admin = User.query.get(admin_id)
    if not admin or not admin.is_admin:
        return jsonify({
            "message": "无管理员权限"
        }), 403

    # 4️⃣ 查询失物信息
    item = LostItem.query.get(item_id)
    if not item:
        return jsonify({
            "message": "失物信息不存在"
        }), 404

    if item.status != '待审核':
        return jsonify({
            "message": "该信息已审核，不能重复操作"
        }), 400

    # 5️⃣ 更新失物状态
    # 再次检查状态，防止并发处理
    if item.status != '待审核':
        return jsonify({
            "message": "该信息已被其他管理员处理"
        }), 400

    if result == '通过':
        item.status = '已发布'
    else:
        item.status = '已驳回'

    # 6️⃣ 记录审核日志
    audit_record = AuditRecord(
        item_id=item_id,
        admin_id=admin_id,
        result=result,
        reason=reason
    )

    db.session.add(audit_record)
    db.session.commit()

    # 7️⃣ 返回结果
    return jsonify({
        "message": "审核完成",
        "item_id": item_id,
        "result": result,
        "current_status": item.status
    }), 200


@admin_bp.route('/pending_items', methods=['GET'])
def get_pending_items():
    # 1️⃣ 获取参数
    admin_id = request.args.get('admin_id')

    # 2️⃣ 校验管理员身份
    if not admin_id:
        return jsonify({"message": "缺少管理员ID"}), 400
    admin = User.query.get(admin_id)
    if not admin or not admin.is_admin:
        return jsonify({"message": "无管理员权限"}), 403

    # 3️⃣ 查询待审核物品
    items = LostItem.query.filter_by(status='待审核').order_by(LostItem.publish_time.desc()).all()

    def build_image_list(image_path):
        if not image_path:
            return []
        return [p for p in image_path.split(',') if p]

    result = []
    for item in items:
        images = build_image_list(item.image_path)
        result.append({
            "item_id": item.item_id,
            "item_name": item.item_name,
            "category": item.category,
            "item_type": item.item_type,
            "location": item.location,
            "event_time": item.event_time.strftime("%Y-%m-%d %H:%M:%S"),
            "description": item.description,
            "status": item.status,
            "publish_time": item.publish_time.strftime("%Y-%m-%d %H:%M:%S") if item.publish_time else None,
            "images": images,                          # 文件名数组
            "image_urls": [f"/uploads/{f}" for f in images]  # 可点击URL
        })

    return jsonify(result), 200


@admin_bp.route('/notifications', methods=['GET'])
def get_notifications():
    admin_id = request.args.get('admin_id')
    if not admin_id:
        return jsonify({"message": "缺少管理员ID"}), 400
    
    admin = User.query.get(admin_id)
    if not admin or not admin.is_admin:
        return jsonify({"message": "无管理员权限"}), 403

    notifications = ClaimNotification.query.filter_by(admin_id=admin_id).order_by(ClaimNotification.created_at.desc()).all()
    
    return jsonify([{
        "notification_id": n.notification_id,
        "item_name": n.claim_request.item.item_name,
        "claimant": n.claim_request.claimant.username,
        "status": n.claim_request.status, # approved or rejected
        "created_at": n.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "is_read": n.is_read
    } for n in notifications]), 200

@admin_bp.route('/notifications/read/<int:notification_id>', methods=['POST'])
def mark_notification_read(notification_id):
    # 简单鉴权略，实际应检查当前用户是否为该通知的所有者
    notification = ClaimNotification.query.get(notification_id)
    if notification:
        notification.is_read = True
        db.session.commit()
    return jsonify({"message": "已标记为已读"}), 200
