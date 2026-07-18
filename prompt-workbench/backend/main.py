import uvicorn  # ASGI服务器
from app import app  # 导入FastAPI应用实例

if __name__ == "__main__":
    # 启动UVicorn服务器，监听所有网络接口，端口8080，开启自动重载
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)  # host="0.0.0.0"（监听所有接口）, port=8080（端口）, reload=True（开发模式自动重载）
