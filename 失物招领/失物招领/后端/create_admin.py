from app import create_app
from app.extensions import db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # 定义要创建的管理员列表
    admins_to_create = [
        {'username': 'admin', 'contact': '13800000000'},
        {'username': 'admin2', 'contact': '13800000002'},
        {'username': 'admin3', 'contact': '13800000003'}
    ]

    for admin_data in admins_to_create:
        # 检查是否已存在管理员
        admin = User.query.filter_by(username=admin_data['username']).first()
        if admin:
            print(f"管理员 {admin_data['username']} 已存在")
        else:
            # 创建管理员
            hashed_password = generate_password_hash('admin123')  # 默认密码
            admin_user = User(
                username=admin_data['username'],
                password=hashed_password,
                contact=admin_data['contact'],
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print(f"管理员 {admin_data['username']} 创建成功")