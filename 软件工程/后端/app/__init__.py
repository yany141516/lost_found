from flask import Flask
from sqlalchemy import text
from app.config import Config
from app.extensions import db
from app.modules.user import user_bp
from app.models import User
from app.modules.lost_item import item_bp
from app.modules.admin import admin_bp
from app.modules.comment import comment_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    app.register_blueprint(user_bp)
    app.register_blueprint(item_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(comment_bp)

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

    return app
