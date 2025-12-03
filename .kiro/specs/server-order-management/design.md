# 设计文档

## 概述

服务器订单管理系统是一个基于Python Flask的Web应用程序，使用SQLite作为文件型数据库。系统提供直观的Web界面用于管理框架协议价格、创建和拆解采购需求、生成EPS订单、查询历史记录以及生成统计报表。数据库文件可以通过云盘（如OneDrive、Dropbox、坚果云等）在多台计算机之间同步。

## 架构

系统采用经典的三层架构：

### 表示层 (Presentation Layer)
- Flask模板引擎渲染HTML页面
- Bootstrap 5提供响应式UI组件
- JavaScript处理客户端交互和表单验证

### 业务逻辑层 (Business Logic Layer)
- Flask路由处理HTTP请求
- 服务类封装业务逻辑（价格计算、订单拆分、统计汇总）
- 数据验证和业务规则执行

### 数据访问层 (Data Access Layer)
- SQLAlchemy ORM映射数据库表
- Repository模式封装数据访问操作
- SQLite数据库文件存储

### 架构图

```
┌─────────────────────────────────────────┐
│         Web Browser (用户界面)           │
└──────────────┬──────────────────────────┘
               │ HTTP
┌──────────────▼──────────────────────────┐
│         Flask Application                │
│  ┌────────────────────────────────────┐ │
│  │  Routes (路由控制器)                │ │
│  └────────┬───────────────────────────┘ │
│           │                              │
│  ┌────────▼───────────────────────────┐ │
│  │  Services (业务逻辑服务)            │ │
│  │  - PriceCalculationService          │ │
│  │  - OrderService                     │ │
│  │  - StatisticsService                │ │
│  └────────┬───────────────────────────┘ │
│           │                              │
│  ┌────────▼───────────────────────────┐ │
│  │  Repositories (数据访问)            │ │
│  │  - SKURepository                    │ │
│  │  - RequirementRepository            │ │
│  │  - OrderRepository                  │ │
│  └────────┬───────────────────────────┘ │
└───────────┼──────────────────────────────┘
            │ SQLAlchemy ORM
┌───────────▼──────────────────────────────┐
│      SQLite Database (文件型数据库)       │
│      server_orders.db                    │
└──────────────────────────────────────────┘
```

## 组件和接口

### 核心组件

#### 1. 数据模型 (Models)

**SKU模型**
```python
class SKU:
    id: int
    sku_code: str (唯一)
    name: str
    unit_price: Decimal
    supplier: str
    category: str
    created_at: datetime
    updated_at: datetime
```

**需求模型**
```python
class Requirement:
    id: int
    requirement_code: str (唯一)
    jira_case: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime
    configurations: List[Configuration]
```

**配置模型**
```python
class Configuration:
    id: int
    requirement_id: int (外键)
    config_name: str
    total_price: Decimal
    created_at: datetime
    items: List[ConfigurationItem]
```

**配置项模型**
```python
class ConfigurationItem:
    id: int
    configuration_id: int (外键)
    sku_id: int (外键)
    quantity: int
    unit_price: Decimal (快照价格)
    subtotal: Decimal
```

**EPS订单模型**
```python
class EPSOrder:
    id: int
    order_code: str (唯一)
    requirement_id: int (外键)
    supplier: str
    total_amount: Decimal
    status: str
    created_at: datetime
    updated_at: datetime
    items: List[EPSOrderItem]
    budget_allocations: List[BudgetAllocation]
```

**EPS订单项模型**
```python
class EPSOrderItem:
    id: int
    order_id: int (外键)
    sku_id: int (外键)
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
```

**预算分配模型**
```python
class BudgetAllocation:
    id: int
    order_id: int (外键)
    budget_code: str
    allocation_percentage: Decimal
    amount: Decimal
```

**价格历史模型**
```python
class PriceHistory:
    id: int
    sku_id: int (外键)
    old_price: Decimal
    new_price: Decimal
    changed_at: datetime
    changed_by: str
```

#### 2. 服务层 (Services)

**PriceCalculationService**
- `calculate_configuration_price(configuration_items)`: 计算配置总价
- `calculate_item_subtotal(sku_id, quantity)`: 计算单项小计
- `get_current_sku_price(sku_id)`: 获取当前SKU价格

**OrderService**
- `create_requirement(data)`: 创建新需求
- `split_requirement_to_orders(requirement_id, supplier_mapping)`: 将需求拆分为EPS订单
- `allocate_budget(order_id, budget_codes)`: 分配预算Code
- `validate_budget_allocation(allocations)`: 验证预算分配比例

**StatisticsService**
- `get_supplier_statistics(start_date, end_date)`: 按供应商统计
- `get_budget_statistics(budget_code)`: 按预算Code统计
- `get_sku_statistics(start_date, end_date)`: 按SKU统计
- `export_to_excel(data, filename)`: 导出统计数据

**DataIntegrityService**
- `check_requirement_dependencies(requirement_id)`: 检查需求依赖
- `archive_price_change(sku_id, old_price, new_price)`: 记录价格变更
- `validate_foreign_keys(entity, references)`: 验证外键关系

#### 3. 数据访问层 (Repositories)

**SKURepository**
- `create(sku_data)`: 创建SKU
- `update(sku_id, sku_data)`: 更新SKU
- `find_by_id(sku_id)`: 按ID查询
- `find_by_code(sku_code)`: 按编码查询
- `search(keyword, supplier)`: 搜索SKU
- `get_all()`: 获取所有SKU

**RequirementRepository**
- `create(requirement_data)`: 创建需求
- `update(requirement_id, requirement_data)`: 更新需求
- `find_by_id(requirement_id)`: 按ID查询
- `find_by_jira_case(jira_case)`: 按Jira Case查询
- `get_all_with_filters(filters)`: 带筛选条件查询

**OrderRepository**
- `create(order_data)`: 创建订单
- `update(order_id, order_data)`: 更新订单
- `find_by_id(order_id)`: 按ID查询
- `find_by_requirement(requirement_id)`: 按需求ID查询
- `find_by_budget_code(budget_code)`: 按预算Code查询
- `get_all_with_filters(filters)`: 带筛选条件查询

#### 4. Web路由 (Routes)

**主页路由**
- `GET /`: 显示主导航页面

**SKU管理路由**
- `GET /skus`: 显示SKU列表
- `GET /skus/new`: 显示创建SKU表单
- `POST /skus`: 创建新SKU
- `GET /skus/<id>/edit`: 显示编辑SKU表单
- `PUT /skus/<id>`: 更新SKU
- `GET /skus/search`: 搜索SKU (AJAX)

**需求管理路由**
- `GET /requirements`: 显示需求列表
- `GET /requirements/new`: 显示创建需求表单
- `POST /requirements`: 创建新需求
- `GET /requirements/<id>`: 显示需求详情
- `POST /requirements/<id>/configurations`: 添加配置方案
- `POST /requirements/<id>/create-orders`: 创建EPS订单

**订单管理路由**
- `GET /orders`: 显示订单列表
- `GET /orders/<id>`: 显示订单详情
- `POST /orders/<id>/budget`: 分配预算Code
- `GET /orders/search`: 查询订单

**统计路由**
- `GET /statistics`: 显示统计页面
- `GET /statistics/supplier`: 供应商统计
- `GET /statistics/budget`: 预算统计
- `GET /statistics/sku`: SKU统计
- `GET /statistics/export`: 导出报表

## 数据模型

### 数据库表结构

**skus表**
```sql
CREATE TABLE skus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    supplier VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**requirements表**
```sql
CREATE TABLE requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    requirement_code VARCHAR(50) UNIQUE NOT NULL,
    jira_case VARCHAR(50) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**configurations表**
```sql
CREATE TABLE configurations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    requirement_id INTEGER NOT NULL,
    config_name VARCHAR(100) NOT NULL,
    total_price DECIMAL(12, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (requirement_id) REFERENCES requirements(id)
);
```

**configuration_items表**
```sql
CREATE TABLE configuration_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    configuration_id INTEGER NOT NULL,
    sku_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(12, 2) NOT NULL,
    FOREIGN KEY (configuration_id) REFERENCES configurations(id),
    FOREIGN KEY (sku_id) REFERENCES skus(id)
);
```

**eps_orders表**
```sql
CREATE TABLE eps_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_code VARCHAR(50) UNIQUE NOT NULL,
    requirement_id INTEGER NOT NULL,
    supplier VARCHAR(100) NOT NULL,
    total_amount DECIMAL(12, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (requirement_id) REFERENCES requirements(id)
);
```

**eps_order_items表**
```sql
CREATE TABLE eps_order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    sku_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(12, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES eps_orders(id),
    FOREIGN KEY (sku_id) REFERENCES skus(id)
);
```

**budget_allocations表**
```sql
CREATE TABLE budget_allocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    budget_code VARCHAR(50) NOT NULL,
    allocation_percentage DECIMAL(5, 2) NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES eps_orders(id)
);
```

**price_history表**
```sql
CREATE TABLE price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku_id INTEGER NOT NULL,
    old_price DECIMAL(10, 2) NOT NULL,
    new_price DECIMAL(10, 2) NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by VARCHAR(50),
    FOREIGN KEY (sku_id) REFERENCES skus(id)
);
```

### 实体关系图

```
┌─────────────┐
│    SKUs     │
└──────┬──────┘
       │
       │ 1:N
       │
┌──────▼──────────────┐      ┌──────────────────┐
│ Configuration Items │◄─────┤ Configurations   │
└─────────────────────┘  N:1 └────────┬─────────┘
                                      │
                                      │ N:1
                                      │
                              ┌───────▼──────────┐
                              │  Requirements    │
                              └───────┬──────────┘
                                      │
                                      │ 1:N
                                      │
                              ┌───────▼──────────┐
                              │   EPS Orders     │
                              └───────┬──────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │ 1:N                           1:N │
         ┌──────────▼────────────┐      ┌──────────▼────────────┐
         │  EPS Order Items      │      │  Budget Allocations   │
         └───────────────────────┘      └───────────────────────┘
```


## 正确性属性

*属性是一个特征或行为，应该在系统的所有有效执行中保持为真——本质上是关于系统应该做什么的正式陈述。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*

### 属性 1: SKU编码唯一性
*对于任何* 两个不同的SKU记录，它们的SKU编码必须不相同，尝试添加重复编码的SKU应该被系统拒绝
**验证需求: 1.2**

### 属性 2: 价格变更历史完整性
*对于任何* SKU的价格修改操作，价格历史表中应该存在一条记录，包含旧价格、新价格和变更时间
**验证需求: 1.3, 8.2**

### 属性 3: SKU搜索结果匹配性
*对于任何* 搜索条件（编码、名称或供应商），返回的所有SKU记录都应该在相应字段中包含该搜索关键字
**验证需求: 1.4**

### 属性 4: 数据持久化往返一致性
*对于任何* 实体（SKU、需求、配置、订单），保存到数据库后重新查询应该返回等价的数据对象
**验证需求: 1.5, 2.5, 3.5, 6.3**

### 属性 5: 需求ID唯一性
*对于任何* 两个不同的需求记录，它们的需求编码必须不相同
**验证需求: 2.1**

### 属性 6: 配置项小计计算正确性
*对于任何* 配置项，其小计金额应该等于SKU单价乘以数量
**验证需求: 2.3**

### 属性 7: 配置总价计算正确性
*对于任何* 配置方案，其总价应该等于所有配置项小计金额之和
**验证需求: 2.4**

### 属性 8: 订单拆分完整性
*对于任何* 需求和供应商选择，拆分生成的所有EPS订单应该包含该需求的所有配置项，且每个配置项只出现在一个订单中
**验证需求: 3.1**

### 属性 9: EPS订单编号唯一性
*对于任何* 两个不同的EPS订单，它们的订单编号必须不相同
**验证需求: 3.2**

### 属性 10: 预算分配比例总和验证
*对于任何* EPS订单的预算分配，所有预算Code的分配比例之和必须等于100%，否则系统应该拒绝保存
**验证需求: 3.4**

### 属性 11: 需求ID筛选完整性
*对于任何* 需求ID筛选操作，返回的所有EPS订单的需求ID字段都应该等于筛选条件中的需求ID
**验证需求: 4.2**

### 属性 12: Jira Case筛选完整性
*对于任何* Jira Case筛选操作，返回的所有需求的Jira Case字段都应该等于筛选条件
**验证需求: 4.3**

### 属性 13: 订单详情查询完整性
*对于任何* EPS订单，查询其详情应该返回所有关联的订单项和预算分配记录
**验证需求: 4.4**

### 属性 14: 预算Code筛选和金额汇总正确性
*对于任何* 预算Code筛选操作，返回的订单总支出应该等于所有使用该预算Code的订单中分配给该Code的金额之和
**验证需求: 4.5**

### 属性 15: 统计聚合计算正确性
*对于任何* 聚合维度（供应商、预算Code、SKU），统计的总金额应该等于该维度下所有订单或订单项的金额之和
**验证需求: 5.1, 5.3, 5.4**

### 属性 16: 时间范围筛选正确性
*对于任何* 时间范围筛选，返回的所有订单的创建时间都应该在指定的开始时间和结束时间之间
**验证需求: 5.2**

### 属性 17: 统计数据导出往返一致性
*对于任何* 统计数据，导出为Excel/CSV后重新解析应该得到等价的数据结构
**验证需求: 5.5**

### 属性 18: 数据库文件外部修改同步
*对于任何* 数据库文件的外部修改，系统重新查询时应该读取到修改后的最新数据
**验证需求: 6.4**

### 属性 19: 表单输入验证
*对于任何* 无效的表单输入（空值、格式错误、超出范围），系统应该拒绝提交并返回明确的错误信息
**验证需求: 7.3, 8.4**

### 属性 20: 操作失败时数据保留
*对于任何* 失败的表单提交操作，用户已输入的有效数据应该被保留在表单中
**验证需求: 7.5**

### 属性 21: 引用完整性约束
*对于任何* 有关联EPS订单的需求，删除操作应该被阻止，或者级联删除所有关联的订单及其子记录
**验证需求: 8.1**

### 属性 22: 外键存在性验证
*对于任何* 创建包含外键的实体（如EPS订单引用需求ID），被引用的实体必须在数据库中存在，否则创建应该失败
**验证需求: 8.3**

### 属性 23: 关联数据查询一致性
*对于任何* 跨表关联查询，返回的所有关联记录都应该在数据库中存在且外键关系正确
**验证需求: 8.5**

## 错误处理

### 错误类型和处理策略

#### 1. 验证错误 (Validation Errors)
- **SKU编码重复**: 返回HTTP 400，提示"SKU编码已存在"
- **预算分配比例不等于100%**: 返回HTTP 400，提示"预算分配比例总和必须为100%"
- **无效的表单输入**: 返回HTTP 400，显示具体字段的错误信息
- **外键不存在**: 返回HTTP 400，提示"关联的记录不存在"

#### 2. 业务逻辑错误 (Business Logic Errors)
- **删除有关联订单的需求**: 返回HTTP 409，提示"该需求存在关联订单，无法删除"或提供级联删除选项
- **订单拆分失败**: 返回HTTP 500，记录详细错误日志

#### 3. 数据库错误 (Database Errors)
- **数据库连接失败**: 返回HTTP 503，提示"数据库连接失败，请稍后重试"
- **数据库文件损坏**: 返回HTTP 500，提示"数据库文件损坏，请检查文件完整性"
- **事务冲突**: 返回HTTP 409，提示"数据已被其他操作修改，请刷新后重试"

#### 4. 系统错误 (System Errors)
- **未捕获的异常**: 返回HTTP 500，记录完整堆栈跟踪，显示通用错误消息
- **文件系统错误**: 返回HTTP 500，提示"文件操作失败"

### 错误处理机制

#### 全局异常处理器
```python
@app.errorhandler(ValidationError)
def handle_validation_error(error):
    return jsonify({'error': str(error)}), 400

@app.errorhandler(BusinessLogicError)
def handle_business_logic_error(error):
    return jsonify({'error': str(error)}), 409

@app.errorhandler(DatabaseError)
def handle_database_error(error):
    logger.error(f"Database error: {error}")
    return jsonify({'error': '数据库操作失败'}), 500

@app.errorhandler(Exception)
def handle_unexpected_error(error):
    logger.exception("Unexpected error occurred")
    return jsonify({'error': '系统错误，请联系管理员'}), 500
```

#### 日志记录
- 所有错误都应该记录到日志文件
- 日志级别：DEBUG（开发）、INFO（正常操作）、WARNING（警告）、ERROR（错误）、CRITICAL（严重错误）
- 日志格式：`[时间] [级别] [模块] - 消息`
- 日志文件位置：`logs/app.log`

#### 用户友好的错误消息
- 避免暴露技术细节和堆栈跟踪
- 提供可操作的建议（如"请检查输入"、"请稍后重试"）
- 使用中文错误消息
- 在开发模式下可以显示详细错误信息

## 测试策略

系统采用双重测试方法，结合单元测试和基于属性的测试，以确保全面的代码覆盖和正确性验证。

### 单元测试

单元测试用于验证特定示例、边缘情况和错误条件：

#### 测试框架
- **pytest**: Python测试框架
- **pytest-flask**: Flask应用测试扩展
- **pytest-cov**: 代码覆盖率报告

#### 单元测试覆盖范围
- **数据模型测试**: 验证模型创建、关系和约束
- **服务层测试**: 测试业务逻辑的特定场景
- **Repository测试**: 验证CRUD操作和查询
- **路由测试**: 测试HTTP端点的请求和响应
- **边缘情况**: 空输入、边界值、特殊字符

#### 示例单元测试
```python
def test_sku_creation():
    """测试SKU创建"""
    sku = SKU(sku_code='SRV001', name='服务器', unit_price=10000, supplier='Dell')
    assert sku.sku_code == 'SRV001'
    assert sku.unit_price == 10000

def test_duplicate_sku_code():
    """测试重复SKU编码被拒绝"""
    sku1 = SKU(sku_code='SRV001', name='服务器1', unit_price=10000, supplier='Dell')
    db.session.add(sku1)
    db.session.commit()
    
    sku2 = SKU(sku_code='SRV001', name='服务器2', unit_price=20000, supplier='HP')
    db.session.add(sku2)
    with pytest.raises(IntegrityError):
        db.session.commit()
```

### 基于属性的测试 (Property-Based Testing)

基于属性的测试用于验证应该在所有输入中保持的通用属性：

#### 测试框架
- **Hypothesis**: Python的基于属性测试库
- 每个属性测试应该运行至少100次迭代

#### 属性测试要求
- 每个正确性属性必须由一个单独的基于属性的测试实现
- 每个测试必须使用注释明确引用设计文档中的正确性属性
- 注释格式：`# Feature: server-order-management, Property {number}: {property_text}`
- 测试应该尽可能避免使用mock，以保持简单性
- 使用智能生成器来约束输入空间

#### 示例属性测试
```python
from hypothesis import given, strategies as st

# Feature: server-order-management, Property 6: 配置项小计计算正确性
@given(
    unit_price=st.decimals(min_value=0.01, max_value=999999.99, places=2),
    quantity=st.integers(min_value=1, max_value=10000)
)
def test_configuration_item_subtotal_calculation(unit_price, quantity):
    """
    对于任何配置项，其小计金额应该等于SKU单价乘以数量
    验证需求: 2.3
    """
    item = ConfigurationItem(unit_price=unit_price, quantity=quantity)
    expected_subtotal = unit_price * quantity
    assert item.calculate_subtotal() == expected_subtotal

# Feature: server-order-management, Property 10: 预算分配比例总和验证
@given(
    allocations=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=20),  # budget_code
            st.decimals(min_value=0.01, max_value=100, places=2)  # percentage
        ),
        min_size=1,
        max_size=5
    )
)
def test_budget_allocation_percentage_sum(allocations):
    """
    对于任何EPS订单的预算分配，所有预算Code的分配比例之和必须等于100%
    验证需求: 3.4
    """
    total_percentage = sum(percentage for _, percentage in allocations)
    
    if abs(total_percentage - 100) > 0.01:  # 允许0.01的浮点误差
        with pytest.raises(ValidationError):
            validate_budget_allocation(allocations)
    else:
        # 应该成功验证
        validate_budget_allocation(allocations)
```

### 集成测试

集成测试验证组件之间的交互：

- **端到端流程测试**: 从创建需求到生成订单的完整流程
- **数据库集成测试**: 验证ORM映射和数据库约束
- **Web界面测试**: 使用Selenium测试关键用户流程

### 测试数据管理

- **测试数据库**: 使用独立的SQLite文件用于测试
- **Fixtures**: 使用pytest fixtures创建测试数据
- **数据清理**: 每个测试后清理数据库
- **测试数据生成**: 使用Hypothesis生成随机但有效的测试数据

### 持续集成

- 所有测试应该在提交前运行
- 目标代码覆盖率：80%以上
- 属性测试应该在CI环境中运行更多迭代（如1000次）

## 性能考虑

### 数据库优化
- 在常用查询字段上创建索引（sku_code, requirement_code, order_code, jira_case, budget_code）
- 使用数据库连接池
- 对大量数据查询使用分页

### 缓存策略
- 缓存SKU列表（框架协议价格变化不频繁）
- 使用Flask-Caching缓存统计查询结果
- 设置合理的缓存过期时间

### 前端优化
- 使用AJAX进行SKU搜索，避免页面刷新
- 对大型表格使用前端分页和排序
- 压缩静态资源（CSS、JavaScript）

## 安全考虑

### 输入验证
- 所有用户输入必须经过验证和清理
- 使用WTForms进行表单验证
- 防止SQL注入（使用ORM参数化查询）
- 防止XSS攻击（模板自动转义）

### 数据保护
- 数据库文件权限设置为仅当前用户可读写
- 敏感操作记录审计日志
- 定期备份数据库文件

### 访问控制
- 基础版本可以不实现用户认证（单用户使用）
- 未来可以添加用户登录和权限管理

## 部署和运维

### 部署方式
- **开发环境**: 直接运行Flask开发服务器
- **生产环境**: 使用Waitress或Gunicorn作为WSGI服务器

### 配置管理
- 使用配置文件管理环境变量
- 支持开发、测试、生产环境配置

### 数据库位置
- 默认位置：`data/server_orders.db`
- 可配置到云盘同步目录（如`~/OneDrive/ServerOrders/server_orders.db`）

### 备份策略
- 建议定期手动备份数据库文件
- 云盘同步提供自动版本历史

### 监控和日志
- 应用日志记录到`logs/app.log`
- 错误日志记录到`logs/error.log`
- 日志文件自动轮转（按大小或日期）

## 技术栈总结

- **后端框架**: Flask 3.0+
- **ORM**: SQLAlchemy 2.0+
- **数据库**: SQLite 3
- **表单处理**: WTForms
- **前端框架**: Bootstrap 5
- **JavaScript**: 原生JavaScript + jQuery（可选）
- **测试框架**: pytest, Hypothesis
- **数据导出**: openpyxl (Excel), csv (CSV)
- **日志**: Python logging模块
- **WSGI服务器**: Waitress (Windows) / Gunicorn (Linux)

## 未来扩展

### 可能的功能增强
- 用户认证和多用户支持
- 角色和权限管理
- 审批工作流
- 邮件通知
- 更丰富的报表和图表
- 移动端适配
- RESTful API支持
- 与Jira系统集成
- 供应商门户

### 技术改进
- 迁移到PostgreSQL或MySQL（如果需要多用户并发）
- 使用Redis缓存
- 前后端分离（Vue.js/React）
- 容器化部署（Docker）
