import os
from sqlalchemy import create_engine  # 创建数据库引擎
from sqlalchemy.orm import sessionmaker  # 会话工厂
from .models import Base  # 导入声明式基类

# 数据库连接URL：SQLite数据库文件路径（使用绝对路径）
# Keep the app database at the project root instead of creating a second copy
# under backend/.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATABASE_URL = f"sqlite:///{os.path.join(PROJECT_ROOT, 'prompt_workbench.db')}"  # SQLite数据库（prompt_workbench.db）

# 创建SQLAlchemy引擎，check_same_thread=False是SQLite必要设置（SQLite默认UTF-8编码）
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}  # check_same_thread=False（SQLite线程安全）
)

# 创建会话工厂，用于创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # autocommit=False（手动提交）, autoflush=False（关闭自动刷新）


def init_db():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)  # 创建所有表结构


def get_db():
    """获取数据库会话的依赖注入函数"""
    db = SessionLocal()  # 创建新会话
    try:
        yield db  # 返回会话给调用者
    finally:
        db.close()  # 确保会话关闭
