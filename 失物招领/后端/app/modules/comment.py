from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import Comment, User, LostItem
from app.utils.security import token_required

comment_bp = Blueprint('comment', __name__)

@comment_bp.route('/add', methods=['POST'])
@token_required
def add_comment():
    data = request.get_json()

    # 1️⃣ 参数获取
    user_id = request.user_id  # 从token获取
    item_id = data.get('item_id')
    content = data.get('content')

    # 2️⃣ 参数校验
    if not all([user_id, item_id, content]):
        return jsonify({'message': '参数不完整'}), 400

    # 检查物品是否存在
    item = LostItem.query.get(item_id)
    if not item:
        return jsonify({"message": "物品不存在"}), 404

    # 3️⃣ 数据库操作
    new_comment = Comment(user_id=user_id, item_id=item_id, content=content)
    db.session.add(new_comment)
    db.session.commit()

    return jsonify({'message': '评论成功'}), 201

@comment_bp.route('/list/<int:item_id>', methods=['GET'])
def get_comments(item_id):
    comments = Comment.query.filter_by(item_id=item_id).order_by(Comment.comment_time).all()
    
    result = []
    for comment in comments:
        import random
        # Use a local Random instance for thread safety
        rng = random.Random(comment.user_id)
        suffix = rng.randint(1000, 9999)
        anonymous_name = f"匿名用户{suffix}"
        
        result.append({
            "comment_id": comment.comment_id,
            "user_id": comment.user_id,
            "username": anonymous_name,
            "content": comment.content,
            "created_at": comment.comment_time.strftime("%Y-%m-%d %H:%M:%S")
        })
        
    return jsonify(result), 200

@comment_bp.route('/delete/<int:comment_id>', methods=['DELETE'])
@token_required
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({"message": "评论不存在"}), 404
    
    # 检查是否是管理员
    current_user = User.query.get(request.user_id)
    is_admin = current_user.is_admin if current_user else False

    if comment.user_id != request.user_id and not is_admin:
        return jsonify({"message": "无权限删除"}), 403
        
    db.session.delete(comment)
    db.session.commit()
    return jsonify({"message": "删除成功"}), 200