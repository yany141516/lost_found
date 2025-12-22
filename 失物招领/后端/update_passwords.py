from app import create_app
from app.extensions import db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    users = User.query.all()
    for user in users:
        if not user.password.startswith('$2b$'):  # 检查是否已经是哈希
            user.password = generate_password_hash(user.password)
            print(f'Updated password for user: {user.username}')
    db.session.commit()
    print('Password update complete')
