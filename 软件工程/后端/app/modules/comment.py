from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import Comment, User, LostItem

comment_bp = Blueprint('comment', __name__, url_prefix='/api/comment')


@comment_bp.route('/add', methods=['POST'])
def add_comment():
    data = request.get_json()

    # 1️⃣ 参数获取
    user_id = data.get('user_id')
    item_id = data.get('item_id')
    content = data.get('content')

    # 2️⃣ 参数校验
    if not all([user_id, item_id, content]):
        return jsonify({
            "message": "缺少必要参数"
        }), 400

    # 3️⃣ 校验用户
    user = User.query.get(user_id)
    if not user:
        return jsonify({
            "message": "用户不存在"
        }), 404

    # 4️⃣ 校验失物信息（只能对已发布留言）
    item = LostItem.query.get(item_id)
    if not item or item.status != '已发布':
        return jsonify({
            "message": "该信息不存在或未发布"
        }), 400

    # 5️⃣ 创建留言
    new_comment = Comment(
        user_id=user_id,
        item_id=item_id,
        content=content
    )

    db.session.add(new_comment)
    db.session.commit()

    # 6️⃣ 返回结果
    return jsonify({
        "message": "留言成功",
        "comment_id": new_comment.comment_id
    }), 201

@comment_bp.route('/list', methods=['GET'])
def list_comments():
    item_id = request.args.get('item_id')

    if not item_id:
        return jsonify({
            "message": "缺少 item_id 参数"
        }), 400

    comments = Comment.query.filter_by(item_id=item_id).order_by(
        Comment.comment_time.asc()
    ).all()

    result = []
    for c in comments:
        result.append({
            "comment_id": c.comment_id,
            "user_id": c.user_id,
            "content": c.content,
            "comment_time": c.comment_time.strftime("%Y-%m-%d %H:%M:%S")
        })

    return jsonify(result), 200
