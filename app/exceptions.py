"""
自定义异常类
"""


class ValidationError(Exception):
    """验证错误异常"""
    def __init__(self, message, field=None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class BusinessLogicError(Exception):
    """业务逻辑错误异常"""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class DatabaseError(Exception):
    """数据库错误异常"""
    def __init__(self, message, original_error=None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class ReferentialIntegrityError(BusinessLogicError):
    """引用完整性错误异常"""
    def __init__(self, message, entity_type=None, entity_id=None, dependent_count=None):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.dependent_count = dependent_count
        super().__init__(message)


class ForeignKeyError(ValidationError):
    """外键验证错误异常"""
    def __init__(self, message, foreign_key_field=None, foreign_key_value=None):
        self.foreign_key_field = foreign_key_field
        self.foreign_key_value = foreign_key_value
        super().__init__(message, field=foreign_key_field)
