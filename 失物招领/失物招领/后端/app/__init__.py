from flask import Flask, send_from_directory
from flask_cors import CORS
from sqlalchemy import text
from app.config import Config
from app.extensions import db
from app.modules.user import user_bp
from app.models import User
from app.modules.lost_item import item_bp
from app.modules.admin import admin_bp
from app.modules.comment import comment_bp
from werkzeug.utils import secure_filename
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')

    db.init_app(app)
    CORS(app)  # 启用CORS支持
    app.register_blueprint(user_bp)
    app.register_blueprint(item_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(comment_bp, url_prefix='/api/comment')

    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    with app.app_context():
        db.create_all()  # 自动创建数据库表

    @app.route("/ping_db")
    def ping_db():
        try:
            # ① 测试数据库连接
            db.session.execute(text("SELECT 1"))

            # ② 测试 ORM 是否生效（你问的这部分）
            User.query.first()

            return {"message": "数据库连接 + ORM 映射均成功 🎉"}
        except Exception as e:
            return {"error": str(e)}, 500

    def serve_file(filename):
        import os
        frontend_path = os.path.join(os.path.dirname(__file__), '..', '..', '前端', 'pages', filename)
        if os.path.exists(frontend_path):
            with open(frontend_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return f"{filename} not found", 404

    @app.route('/')
    def index():
        # Serve home.html as default
        return serve_file('home.html')

    @app.route('/login')
    def login():
        return serve_file('login.html')

    # 登录API路由（用于前端fetch登录请求）
    @app.route('/api/user/login', methods=['POST'])
    def api_login():
        from app.modules.user import login
        return login()

    @app.route('/home')
    def home():
        return serve_file('home.html')

    @app.route('/publish')
    def publish():
        return serve_file('publish.html')

    @app.route('/profile')
    def profile():
        return serve_file('profile.html')

    @app.route('/detail')
    def detail():
        return serve_file('detail.html')

    return app
