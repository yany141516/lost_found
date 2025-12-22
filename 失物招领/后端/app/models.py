from app.extensions import db


class User(db.Model):
    __tablename__ = 'user'

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    contact = db.Column(db.String(100), nullable=False, unique=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    # 关系（可选，用于反向查询）
    items = db.relationship('LostItem', backref='user', lazy=True)
    comments = db.relationship('Comment', backref='user', lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"


class LostItem(db.Model):
    __tablename__ = 'lost_item'

    item_id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False)
    category = db.Column(
        db.Enum('证件', '电子设备', '衣物', '书籍', '其他'),
        nullable=False
    )
    description = db.Column(db.Text)
    location = db.Column(db.String(100), nullable=False)
    event_time = db.Column(db.DateTime, nullable=False)
    item_type = db.Column(
        db.Enum('丢失', '拾获'),
        nullable=False
    )
    image_path = db.Column(db.String(255))
    status = db.Column(
        db.Enum('待审核', '已发布', '已认领', '已驳回'),
        default='待审核'
    )
    publish_time = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.user_id'),
        nullable=False
    )

    comments = db.relationship('Comment', backref='item', lazy=True)
    audits = db.relationship('AuditRecord', backref='item', lazy=True)

    def __repr__(self):
        return f"<LostItem {self.item_name}>"


class AuditRecord(db.Model):
    __tablename__ = 'audit_record'

    audit_id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(
        db.Integer,
        db.ForeignKey('lost_item.item_id', ondelete='CASCADE'),
        nullable=False
    )
    admin_id = db.Column(
        db.Integer,
        db.ForeignKey('user.user_id'),
        nullable=False
    )
    result = db.Column(
        db.Enum('通过', '驳回'),
        nullable=False
    )
    reason = db.Column(db.String(255))
    audit_time = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    def __repr__(self):
        return f"<AuditRecord item={self.item_id} result={self.result}>"


class Comment(db.Model):
    __tablename__ = 'comment'

    comment_id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(
        db.Integer,
        db.ForeignKey('lost_item.item_id', ondelete='CASCADE'),
        nullable=False
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.user_id', ondelete='CASCADE'),
        nullable=False
    )
    content = db.Column(db.String(200), nullable=False)
    comment_time = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    def __repr__(self):
        return f"<Comment {self.comment_id}>"


class ClaimRequest(db.Model):
    __tablename__ = 'claim_request'

    claim_id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('lost_item.item_id'), nullable=False)
    claimant_user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    message = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum('pending', 'approved', 'rejected'), default='pending')
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    item = db.relationship('LostItem', backref='claim_requests')
    claimant = db.relationship('User', backref='claim_requests')
