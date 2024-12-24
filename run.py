from app import create_app

if __name__ == '__main__':
    app = create_app()  # 创建应用实例
    app.run(debug=True, host='0.0.0.0', port=5003)  # 启动服务器
