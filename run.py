"""
应用启动脚本
"""
import os
from app import create_app

# 从环境变量获取配置，默认使用开发环境
config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    # 开发环境使用Flask开发服务器
    if config_name == 'development':
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        # 生产环境建议使用Waitress或Gunicorn
        print("生产环境请使用 Waitress 或 Gunicorn 运行应用")
        print("例如: waitress-serve --host=0.0.0.0 --port=5000 run:app")
