from cryptography.fernet import Fernet  # Fernet对称加密（对称加密）
import os  # 文件系统（文件系统）

KEY_FILE = "encryption_key.key"  # 密钥文件（密钥文件）


def load_or_generate_key():
    """加载或生成加密密钥（加载密钥）"""
    if os.path.exists(KEY_FILE):  # 检查密钥文件存在（检查存在）
        with open(KEY_FILE, "rb") as f:
            return f.read()  # 读取密钥（读取）
    else:
        key = Fernet.generate_key()  # 生成新密钥（生成）
        with open(KEY_FILE, "wb") as f:
            f.write(key)  # 保存密钥（保存）
        return key  # 返回密钥（返回）


fernet = Fernet(load_or_generate_key())  # 创建Fernet实例（创建实例）


def encrypt_api_key(api_key: str) -> str:
    """加密API密钥（加密密钥）"""
    if not api_key:  # 检查空值（检查）
        return ""  # 返回空（空）
    return fernet.encrypt(api_key.encode()).decode()  # 加密并返回（加密）


def decrypt_api_key(encrypted_key: str) -> str:
    """解密API密钥（解密密钥）"""
    if not encrypted_key:  # 检查空值（检查）
        return ""  # 返回空（空）
    return fernet.decrypt(encrypted_key.encode()).decode()  # 解密并返回（解密）
