"""
订单管理路由
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from decimal import Decimal

from app import db
from app.repositories.order_repository import OrderRepository
from app.repositories.requirement_repository import RequirementRepository
from app.services.order_service import OrderService

order_bp = Blueprint('order', __name__, url_prefix='/orders')


@order_bp.route('/')
def list_orders():
    """显示订单列表"""
    # 获取筛选参数
    filters = {}
    if request.args.get('requirement_id'):
        filters['requirement_id'] = int(request.args.get('requirement_id'))
    if request.args.get('supplier'):
        filters['supplier'] = request.args.get('supplier')
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    if request.args.get('order_code'):
        filters['order_code'] = request.args.get('order_code')
    if request.args.get('jira_case'):
        filters['jira_case'] = request.args.get('jira_case')
    if request.args.get('budget_code'):
        filters['budget_code'] = request.args.get('budget_code')
    if request.args.get('sort_by'):
        filters['sort_by'] = request.args.get('sort_by')
    
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # 查询订单
    pagination = OrderRepository.get_all_with_filters(filters if filters else None, page=page, per_page=per_page)
    
    return render_template('order/list.html', orders=pagination.items, pagination=pagination, filters=filters)


@order_bp.route('/<int:order_id>')
def view_order(order_id):
    """显示订单详情"""
    try:
        order_details = OrderService.get_order_details(order_id)
        return render_template('order/detail.html', **order_details)
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('order.list_orders'))


@order_bp.route('/create', methods=['GET', 'POST'])
def create_order():
    """创建订单"""
    if request.method == 'GET':
        # 获取所有需求用于选择
        requirements = RequirementRepository.get_all_with_filters()
        return render_template('order/form.html', requirements=requirements)
    
    try:
        # 从需求创建订单
        requirement_id = int(request.form.get('requirement_id'))
        
        # 获取供应商映射（如果提供）
        supplier_mapping = {}
        # 这里可以从表单获取配置到供应商的映射
        # 暂时使用默认逻辑（从SKU获取供应商）
        
        orders = OrderService.split_requirement_to_orders(requirement_id, supplier_mapping)
        
        flash(f'成功创建 {len(orders)} 个订单', 'success')
        return redirect(url_for('order.list_orders'))
        
    except ValueError as e:
        flash(str(e), 'error')
        requirements = RequirementRepository.get_all_with_filters()
        return render_template('order/form.html', requirements=requirements)
    except Exception as e:
        db.session.rollback()
        flash(f'创建订单失败: {str(e)}', 'error')
        requirements = RequirementRepository.get_all_with_filters()
        return render_template('order/form.html', requirements=requirements)


@order_bp.route('/<int:order_id>/budget', methods=['GET', 'POST'])
def manage_budget(order_id):
    """管理订单预算分配"""
    order = OrderRepository.find_by_id(order_id)
    if not order:
        flash('订单不存在', 'error')
        return redirect(url_for('order.list_orders'))
    
    if request.method == 'GET':
        # 显示预算分配表单
        budget_allocations = OrderRepository.get_budget_allocations(order_id)
        return render_template('order/budget.html', order=order, budget_allocations=budget_allocations)
    
    try:
        # 处理预算分配提交
        allocations_data = []
        
        # 从表单获取预算分配数据
        budget_codes = request.form.getlist('budget_code[]')
        percentages = request.form.getlist('allocation_percentage[]')
        
        for budget_code, percentage in zip(budget_codes, percentages):
            if budget_code and percentage:
                allocations_data.append({
                    'budget_code': budget_code,
                    'allocation_percentage': Decimal(percentage)
                })
        
        # 分配预算
        OrderService.allocate_budget(order_id, allocations_data)
        
        flash('预算分配成功', 'success')
        return redirect(url_for('order.view_order', order_id=order_id))
        
    except ValueError as e:
        flash(str(e), 'error')
        budget_allocations = OrderRepository.get_budget_allocations(order_id)
        return render_template('order/budget.html', order=order, budget_allocations=budget_allocations)
    except Exception as e:
        db.session.rollback()
        flash(f'预算分配失败: {str(e)}', 'error')
        budget_allocations = OrderRepository.get_budget_allocations(order_id)
        return render_template('order/budget.html', order=order, budget_allocations=budget_allocations)


@order_bp.route('/<int:order_id>/edit', methods=['GET', 'POST'])
def edit_order(order_id):
    """编辑订单"""
    order = OrderRepository.find_by_id(order_id)
    if not order:
        flash('订单不存在', 'error')
        return redirect(url_for('order.list_orders'))
    
    if request.method == 'GET':
        return render_template('order/edit.html', order=order)
    
    try:
        order_data = {}
        
        if request.form.get('order_code'):
            order_data['order_code'] = request.form.get('order_code')
        if request.form.get('supplier'):
            order_data['supplier'] = request.form.get('supplier')
        if request.form.get('status'):
            order_data['status'] = request.form.get('status')
        
        OrderRepository.update(order_id, order_data)
        
        flash('订单更新成功', 'success')
        return redirect(url_for('order.view_order', order_id=order_id))
        
    except ValueError as e:
        flash(str(e), 'error')
        return render_template('order/edit.html', order=order)
    except Exception as e:
        db.session.rollback()
        flash(f'更新订单失败: {str(e)}', 'error')
        return render_template('order/edit.html', order=order)


@order_bp.route('/search')
def search_orders():
    """搜索订单（AJAX接口）"""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify([])
    
    # 按订单编号搜索
    orders = OrderRepository.get_all_with_filters({'order_code': query})
    
    results = []
    for order in orders[:10]:  # 限制返回10条
        results.append({
            'id': order.id,
            'order_code': order.order_code,
            'supplier': order.supplier,
            'total_amount': float(order.total_amount),
            'status': order.status
        })
    
    return jsonify(results)
