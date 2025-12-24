import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///d:/失物招领/后端/instance/lost_found.db'  # 指定数据库路径
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'your_fixed_secret_key_here'  # 固定密钥，避免重启后token失效
