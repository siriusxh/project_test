"""
需求管理路由
"""
from decimal import Decimal

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

from app import db
from app.models.requirement import Requirement, Configuration, ConfigurationItem
from app.repositories.requirement_repository import RequirementRepository
from app.repositories.configuration_repository import ConfigurationRepository
from app.repositories.sku_repository import SKURepository
from app.services.price_calculation_service import PriceCalculationService

requirement_bp = Blueprint('requirement', __name__, url_prefix='/requirements')


@requirement_bp.route('/')
def list_requirements():
    """显示需求列表"""
    filters = {}
    
    # 获取筛选参数
    jira_case = request.args.get('jira_case')
    status = request.args.get('status')
    requirement_code = request.args.get('requirement_code')
    
    if jira_case:
        filters['jira_case'] = jira_case
    if status:
        filters['status'] = status
    if requirement_code:
        filters['requirement_code'] = requirement_code
    
    requirements = RequirementRepository.get_all_with_filters(filters)
    
    return render_template('requirement/list.html', requirements=requirements)


@requirement_bp.route('/new')
def new_requirement():
    """显示创建需求表单"""
    return render_template('requirement/form.html', requirement=None)


@requirement_bp.route('/', methods=['POST'])
def create_requirement():
    """创建新需求"""
    try:
        requirement_data = {
            'requirement_code': request.form.get('requirement_code'),
            'jira_case': request.form.get('jira_case'),
            'description': request.form.get('description'),
            'status': request.form.get('status', 'draft')
        }
        
        # 验证必填字段
        if not requirement_data['requirement_code']:
            flash('需求编码不能为空', 'error')
            return render_template('requirement/form.html', requirement=None, form_data=request.form)
        
        if not requirement_data['jira_case']:
            flash('Jira Case不能为空', 'error')
            return render_template('requirement/form.html', requirement=None, form_data=request.form)
        
        requirement = RequirementRepository.create(requirement_data)
        
        flash(f'需求 {requirement.requirement_code} 创建成功', 'success')
        return redirect(url_for('requirement.view_requirement', requirement_id=requirement.id))
    
    except ValueError as e:
        flash(str(e), 'error')
        return render_template('requirement/form.html', requirement=None, form_data=request.form)
    except Exception as e:
        flash(f'创建需求失败: {str(e)}', 'error')
        return render_template('requirement/form.html', requirement=None, form_data=request.form)


@requirement_bp.route('/<int:requirement_id>')
def view_requirement(requirement_id):
    """显示需求详情"""
    requirement = RequirementRepository.find_by_id(requirement_id)
    if not requirement:
        flash('需求不存在', 'error')
        return redirect(url_for('requirement.list_requirements'))
    
    # 获取所有配置
    configurations = ConfigurationRepository.find_by_requirement(requirement_id)
    
    # 获取所有SKU用于下拉选择
    skus = SKURepository.get_all()
    
    return render_template('requirement/detail.html', 
                         requirement=requirement, 
                         configurations=configurations,
                         skus=skus)


@requirement_bp.route('/<int:requirement_id>/edit')
def edit_requirement(requirement_id):
    """显示编辑需求表单"""
    requirement = RequirementRepository.find_by_id(requirement_id)
    if not requirement:
        flash('需求不存在', 'error')
        return redirect(url_for('requirement.list_requirements'))
    
    return render_template('requirement/form.html', requirement=requirement)


@requirement_bp.route('/<int:requirement_id>', methods=['PUT', 'POST'])
def update_requirement(requirement_id):
    """更新需求"""
    try:
        requirement_data = {
            'requirement_code': request.form.get('requirement_code'),
            'jira_case': request.form.get('jira_case'),
            'description': request.form.get('description'),
            'status': request.form.get('status')
        }
        
        requirement = RequirementRepository.update(requirement_id, requirement_data)
        
        flash(f'需求 {requirement.requirement_code} 更新成功', 'success')
        return redirect(url_for('requirement.view_requirement', requirement_id=requirement.id))
    
    except ValueError as e:
        flash(str(e), 'error')
        requirement = RequirementRepository.find_by_id(requirement_id)
        return render_template('requirement/form.html', requirement=requirement, form_data=request.form)
    except Exception as e:
        flash(f'更新需求失败: {str(e)}', 'error')
        requirement = RequirementRepository.find_by_id(requirement_id)
        return render_template('requirement/form.html', requirement=requirement, form_data=request.form)


@requirement_bp.route('/<int:requirement_id>/configurations', methods=['POST'])
def add_configuration(requirement_id):
    """添加配置方案"""
    try:
        # 验证需求是否存在
        requirement = RequirementRepository.find_by_id(requirement_id)
        if not requirement:
            return jsonify({'error': '需求不存在'}), 404
        
        # 获取配置数据
        config_name = request.form.get('config_name')
        if not config_name:
            return jsonify({'error': '配置名称不能为空'}), 400
        
        # 获取配置项数据
        items_data = []
        sku_ids = request.form.getlist('sku_id[]')
        quantities = request.form.getlist('quantity[]')
        
        if not sku_ids or not quantities:
            return jsonify({'error': '配置项不能为空'}), 400
        
        for sku_id, quantity in zip(sku_ids, quantities):
            if not sku_id or not quantity:
                continue
            
            sku_id = int(sku_id)
            quantity = int(quantity)
            
            # 获取当前SKU价格
            unit_price = PriceCalculationService.get_current_sku_price(sku_id)
            if unit_price is None:
                return jsonify({'error': f'SKU ID {sku_id} 不存在'}), 400
            
            items_data.append({
                'sku_id': sku_id,
                'quantity': quantity,
                'unit_price': unit_price
            })
        
        if not items_data:
            return jsonify({'error': '至少需要一个配置项'}), 400
        
        # 创建配置及配置项
        configuration_data = {
            'requirement_id': requirement_id,
            'config_name': config_name
        }
        
        configuration = ConfigurationRepository.create_with_items(configuration_data, items_data)
        
        flash(f'配置 {config_name} 添加成功', 'success')
        return redirect(url_for('requirement.view_requirement', requirement_id=requirement_id))
    
    except Exception as e:
        flash(f'添加配置失败: {str(e)}', 'error')
        return redirect(url_for('requirement.view_requirement', requirement_id=requirement_id))


@requirement_bp.route('/api/calculate-price', methods=['POST'])
def calculate_price():
    """计算配置价格（AJAX接口）"""
    try:
        data = request.get_json()
        items = data.get('items', [])
        
        if not items:
            return jsonify({'error': '配置项不能为空'}), 400
        
        total_price = PriceCalculationService.calculate_configuration_price(items)
        
        # 计算每项的小计
        items_with_subtotal = []
        for item in items:
            unit_price = PriceCalculationService.get_current_sku_price(item['sku_id'])
            subtotal = PriceCalculationService.calculate_item_subtotal(unit_price, item['quantity'])
            items_with_subtotal.append({
                'sku_id': item['sku_id'],
                'quantity': item['quantity'],
                'unit_price': float(unit_price),
                'subtotal': float(subtotal)
            })
        
        return jsonify({
            'total_price': float(total_price),
            'items': items_with_subtotal
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400
