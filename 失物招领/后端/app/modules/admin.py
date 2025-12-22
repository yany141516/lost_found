from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import User, LostItem, AuditRecord

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
