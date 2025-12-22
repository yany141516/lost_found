from app import create_app
from app.models import User

app = create_app()
with app.app_context():
    users = User.query.all()
    print(f'Total users: {len(users)}')
    for user in users:
        print(f'User: {user.username}, Password starts with: {user.password[:10]}...')
