"""参数校验装饰器"""
import os
from functools import wraps
from flask import request
from utils.response import error_response
from utils.data_store import read_json
import config


def validate_company_exists(f):
    """校验公司是否存在"""
    @wraps(f)
    def wrapper(company_id, *args, **kwargs):
        companies = read_json(os.path.join(config.DATA_DIR, "companies.json"))
        found = any(c["company_id"] == company_id for c in companies)
        if not found:
            return error_response(
                "COMPANY_NOT_FOUND", "公司不存在", 404,
                {"company_id": company_id}
            )
        return f(company_id, *args, **kwargs)
    return wrapper


def validate_required_fields(required_fields):
    """校验请求体必填字段"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            body = request.get_json(silent=True) or {}
            missing = [field for field in required_fields if field not in body]
            if missing:
                return error_response(
                    "INVALID_FINANCIAL_DATA", "财务数据格式不合法或缺少必填字段", 400,
                    {"missing_fields": missing}
                )
            return f(*args, **kwargs)
        return wrapper
    return decorator
