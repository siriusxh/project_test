"""
SKU管理路由
"""
from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

from app.repositories import SKURepository

sku_bp = Blueprint('sku', __name__, url_prefix='/skus')


@sku_bp.route('/')
def list_skus():
    """显示SKU列表"""
    keyword = request.args.get('keyword', '').strip()
    supplier = request.args.get('supplier', '').strip()
    
    if keyword or supplier:
        skus = SKURepository.search(keyword=keyword or None, supplier=supplier or None)
    else:
        skus = SKURepository.get_all()
    
    return render_template('sku/list.html', skus=skus, keyword=keyword, supplier=supplier)


@sku_bp.route('/new')
def new_sku():
    """显示创建SKU表单"""
    return render_template('sku/form.html', sku=None)


@sku_bp.route('/', methods=['POST'])
def create_sku():
    """创建新SKU"""
    try:
        sku_data = {
            'sku_code': request.form.get('sku_code', '').strip(),
            'name': request.form.get('name', '').strip(),
            'unit_price': Decimal(request.form.get('unit_price', '0')),
            'supplier': request.form.get('supplier', '').strip(),
            'category': request.form.get('category', '').strip() or None
        }
        
        # 验证必填字段
        if not sku_data['sku_code']:
            flash('SKU编码不能为空', 'error')
            return render_template('sku/form.html', sku=None, form_data=request.form)
        
        if not sku_data['name']:
            flash('SKU名称不能为空', 'error')
            return render_template('sku/form.html', sku=None, form_data=request.form)
        
        if not sku_data['supplier']:
            flash('供应商不能为空', 'error')
            return render_template('sku/form.html', sku=None, form_data=request.form)
        
        if sku_data['unit_price'] <= 0:
            flash('单价必须大于0', 'error')
            return render_template('sku/form.html', sku=None, form_data=request.form)
        
        sku = SKURepository.create(sku_data)
        flash(f'SKU {sku.sku_code} 创建成功', 'success')
        return redirect(url_for('sku.list_skus'))
        
    except ValueError as e:
        flash(str(e), 'error')
        return render_template('sku/form.html', sku=None, form_data=request.form)
    except InvalidOperation:
        flash('单价格式错误', 'error')
        return render_template('sku/form.html', sku=None, form_data=request.form)
    except Exception as e:
        flash(f'创建失败: {str(e)}', 'error')
        return render_template('sku/form.html', sku=None, form_data=request.form)


@sku_bp.route('/<int:sku_id>/edit')
def edit_sku(sku_id):
    """显示编辑SKU表单"""
    sku = SKURepository.find_by_id(sku_id)
    if not sku:
        flash('SKU不存在', 'error')
        return redirect(url_for('sku.list_skus'))
    
    price_history = SKURepository.get_price_history(sku_id)
    return render_template('sku/form.html', sku=sku, price_history=price_history)


@sku_bp.route('/<int:sku_id>', methods=['POST'])
def update_sku(sku_id):
    """更新SKU"""
    try:
        sku_data = {
            'sku_code': request.form.get('sku_code', '').strip(),
            'name': request.form.get('name', '').strip(),
            'unit_price': Decimal(request.form.get('unit_price', '0')),
            'supplier': request.form.get('supplier', '').strip(),
            'category': request.form.get('category', '').strip() or None
        }
        
        # 验证必填字段
        if not sku_data['sku_code']:
            flash('SKU编码不能为空', 'error')
            return redirect(url_for('sku.edit_sku', sku_id=sku_id))
        
        if not sku_data['name']:
            flash('SKU名称不能为空', 'error')
            return redirect(url_for('sku.edit_sku', sku_id=sku_id))
        
        if not sku_data['supplier']:
            flash('供应商不能为空', 'error')
            return redirect(url_for('sku.edit_sku', sku_id=sku_id))
        
        if sku_data['unit_price'] <= 0:
            flash('单价必须大于0', 'error')
            return redirect(url_for('sku.edit_sku', sku_id=sku_id))
        
        changed_by = request.form.get('changed_by', 'system')
        sku = SKURepository.update(sku_id, sku_data, changed_by=changed_by)
        flash(f'SKU {sku.sku_code} 更新成功', 'success')
        return redirect(url_for('sku.list_skus'))
        
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('sku.edit_sku', sku_id=sku_id))
    except InvalidOperation:
        flash('单价格式错误', 'error')
        return redirect(url_for('sku.edit_sku', sku_id=sku_id))
    except Exception as e:
        flash(f'更新失败: {str(e)}', 'error')
        return redirect(url_for('sku.edit_sku', sku_id=sku_id))


@sku_bp.route('/<int:sku_id>/delete', methods=['POST'])
def delete_sku(sku_id):
    """删除SKU"""
    try:
        if SKURepository.delete(sku_id):
            flash('SKU删除成功', 'success')
        else:
            flash('SKU不存在', 'error')
    except Exception as e:
        flash(f'删除失败: {str(e)}', 'error')
    
    return redirect(url_for('sku.list_skus'))


@sku_bp.route('/search')
def search_skus_ajax():
    """SKU搜索AJAX接口"""
    keyword = request.args.get('keyword', '').strip()
    supplier = request.args.get('supplier', '').strip()
    
    skus = SKURepository.search(keyword=keyword or None, supplier=supplier or None)
    
    return jsonify({
        'success': True,
        'data': [sku.to_dict() for sku in skus]
    })
