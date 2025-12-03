"""
属性测试: 操作失败时数据保留
Feature: server-order-management, Property 20: 操作失败时数据保留
验证需求: 7.5
"""
import pytest
from decimal import Decimal
from hypothesis import given, strategies as st, settings, HealthCheck

from app import create_app, db
from app.models import SKU, Requirement


@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


# Feature: server-order-management, Property 20: 操作失败时数据保留
@given(
    sku_code=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    name=st.text(min_size=1, max_size=200, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))).filter(lambda x: x.strip()),
    unit_price=st.decimals(min_value=Decimal('0.01'), max_value=Decimal('999999.99'), places=2),
    supplier=st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))).filter(lambda x: x.strip()),
    category=st.one_of(st.none(), st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_sku_form_data_retention_on_duplicate_error(client, sku_code, name, unit_price, supplier, category):
    """
    对于任何失败的SKU创建操作（重复编码），用户已输入的有效数据应该被保留在表单中
    验证需求: 7.5
    """
    with client.application.app_context():
        # 清理可能存在的重复数据
        existing = SKU.query.filter_by(sku_code=sku_code).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
        
        # 先创建一个SKU以触发重复错误
        existing_sku = SKU(
            sku_code=sku_code,
            name='Existing SKU',
            unit_price=Decimal('100.00'),
            supplier='Existing Supplier',
            category='Server'
        )
        db.session.add(existing_sku)
        db.session.commit()
    
    # 尝试创建重复的SKU
    form_data = {
        'sku_code': sku_code,  # 重复的编码
        'name': name,
        'unit_price': str(unit_price),
        'supplier': supplier,
        'category': category if category else ''
    }
    
    response = client.post('/skus/', data=form_data, follow_redirects=False)
    
    # 验证返回的页面包含用户输入的数据
    response_text = response.get_data(as_text=True)
    
    # 表单应该保留用户输入的数据
    assert name in response_text or 'value="' + name + '"' in response_text or "value='" + name + "'" in response_text
    assert supplier in response_text or 'value="' + supplier + '"' in response_text or "value='" + supplier + "'" in response_text
    assert str(unit_price) in response_text
    
    # 应该显示错误消息
    assert 'SKU编码已存在' in response_text or '已存在' in response_text or 'error' in response_text.lower()


# Feature: server-order-management, Property 20: 操作失败时数据保留
@given(
    sku_code=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    name=st.text(min_size=1, max_size=200, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))),
    supplier=st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))),
    category=st.one_of(st.none(), st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_sku_form_data_retention_on_validation_error(client, sku_code, name, supplier, category):
    """
    对于任何失败的SKU创建操作（验证错误），用户已输入的有效数据应该被保留在表单中
    验证需求: 7.5
    """
    # 提交无效的单价（负数或零）
    form_data = {
        'sku_code': sku_code,
        'name': name,
        'unit_price': '-10.00',  # 无效的单价
        'supplier': supplier,
        'category': category if category else ''
    }
    
    response = client.post('/skus/', data=form_data, follow_redirects=False)
    
    # 验证返回的页面包含用户输入的数据
    response_text = response.get_data(as_text=True)
    
    # 表单应该保留用户输入的有效数据
    assert sku_code in response_text or 'value="' + sku_code + '"' in response_text
    assert name in response_text or 'value="' + name + '"' in response_text
    assert supplier in response_text or 'value="' + supplier + '"' in response_text
    
    # 应该显示错误消息
    assert '单价' in response_text or 'error' in response_text.lower()


# Feature: server-order-management, Property 20: 操作失败时数据保留
@given(
    requirement_code=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    jira_case=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pd'))),
    description=st.one_of(st.none(), st.text(max_size=500))
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_requirement_form_data_retention_on_duplicate_error(client, requirement_code, jira_case, description):
    """
    对于任何失败的需求创建操作（重复编码），用户已输入的有效数据应该被保留在表单中
    验证需求: 7.5
    """
    with client.application.app_context():
        # 清理可能存在的重复数据
        existing = Requirement.query.filter_by(requirement_code=requirement_code).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
        
        # 先创建一个需求以触发重复错误
        existing_req = Requirement(
            requirement_code=requirement_code,
            jira_case='EXISTING-001',
            description='Existing requirement',
            status='draft'
        )
        db.session.add(existing_req)
        db.session.commit()
    
    # 尝试创建重复的需求
    form_data = {
        'requirement_code': requirement_code,  # 重复的编码
        'jira_case': jira_case,
        'description': description if description else '',
        'status': 'draft'
    }
    
    response = client.post('/requirements/', data=form_data, follow_redirects=False)
    
    # 验证返回的页面包含用户输入的数据
    response_text = response.get_data(as_text=True)
    
    # 表单应该保留用户输入的数据
    assert jira_case in response_text or 'value="' + jira_case + '"' in response_text
    if description:
        # HTML会转义特殊字符，需要检查多种转义格式
        # Jinja2可能使用&#34;而不是&quot;来转义双引号
        import html
        escaped_description = html.escape(description)
        # 也检查数字实体编码（注意：&必须最先替换）
        numeric_escaped = description.replace('&', '&amp;').replace('"', '&#34;').replace("'", '&#39;').replace('<', '&lt;').replace('>', '&gt;')
        assert description in response_text or escaped_description in response_text or numeric_escaped in response_text
    
    # 应该显示错误消息
    assert '需求编码已存在' in response_text or '已存在' in response_text or 'error' in response_text.lower()


# Feature: server-order-management, Property 20: 操作失败时数据保留
@given(
    jira_case=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pd'))),
    description=st.one_of(st.none(), st.text(max_size=500))
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_requirement_form_data_retention_on_validation_error(client, jira_case, description):
    """
    对于任何失败的需求创建操作（验证错误），用户已输入的有效数据应该被保留在表单中
    验证需求: 7.5
    """
    # 提交缺少必填字段的表单
    form_data = {
        'requirement_code': '',  # 缺少必填字段
        'jira_case': jira_case,
        'description': description if description else '',
        'status': 'draft'
    }
    
    response = client.post('/requirements/', data=form_data, follow_redirects=False)
    
    # 验证返回的页面包含用户输入的数据
    response_text = response.get_data(as_text=True)
    
    # 表单应该保留用户输入的有效数据
    assert jira_case in response_text or 'value="' + jira_case + '"' in response_text
    if description:
        # HTML会转义特殊字符，需要检查多种转义格式
        # Jinja2可能使用&#34;而不是&quot;来转义双引号
        import html
        escaped_description = html.escape(description)
        # 也检查数字实体编码（注意：&必须最先替换）
        numeric_escaped = description.replace('&', '&amp;').replace('"', '&#34;').replace("'", '&#39;').replace('<', '&lt;').replace('>', '&gt;')
        assert description in response_text or escaped_description in response_text or numeric_escaped in response_text
    
    # 应该显示错误消息
    assert '需求编码' in response_text or 'error' in response_text.lower()
