# 服务器订单管理系统

基于Flask的服务器订单管理Web应用程序，用于管理框架协议价格、采购需求、EPS订单和预算分配。

## 功能特性

- SKU和框架协议价格管理
- 采购需求创建和配置拆解
- EPS订单生成和预算分配
- 订单查询和多维度筛选
- 统计汇总和报表导出
- 文件型数据库支持云盘同步

## 技术栈

- **后端**: Flask 3.0, SQLAlchemy 2.0
- **数据库**: SQLite 3
- **前端**: Bootstrap 5
- **测试**: pytest, Hypothesis

## 安装步骤

1. 克隆项目到本地

2. 创建虚拟环境：
```bash
python -m venv venv
```

3. 激活虚拟环境：
- Windows: `venv\Scripts\activate`
- Linux/Mac: `source venv/bin/activate`

4. 安装依赖：
```bash
pip install -r requirements.txt
```

## 运行应用

### 开发环境

```bash
python run.py
```

应用将在 http://localhost:5000 启动

### 生产环境

使用Waitress（推荐Windows）：
```bash
waitress-serve --host=0.0.0.0 --port=5000 run:app
```

或使用Gunicorn（Linux）：
```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## 配置

### 环境变量

- `FLASK_ENV`: 环境配置 (development/production/testing)
- `SECRET_KEY`: Flask密钥（生产环境必须设置）

### 数据库位置

默认数据库文件位置：`data/server_orders.db`

如需使用云盘同步，可在 `config.py` 中修改 `DATABASE_FILE` 路径。

## 项目结构

```
.
├── app/                    # 应用主目录
│   ├── __init__.py        # 应用工厂函数
│   ├── models/            # 数据模型
│   ├── services/          # 业务逻辑服务
│   ├── repositories/      # 数据访问层
│   ├── templates/         # HTML模板
│   └── static/            # 静态文件
├── data/                  # 数据库文件目录
├── logs/                  # 日志文件目录
├── config.py              # 配置文件
├── run.py                 # 启动脚本
└── requirements.txt       # 依赖列表
```

## 测试

运行所有测试：
```bash
pytest
```

运行带覆盖率的测试：
```bash
pytest --cov=app
```

## 开发计划

详见 `.kiro/specs/server-order-management/` 目录下的规范文档：
- `requirements.md` - 需求文档
- `design.md` - 设计文档
- `tasks.md` - 实施计划

## 许可证

内部使用项目
