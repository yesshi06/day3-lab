"""统一响应格式工具"""
import uuid
from flask import jsonify


def _trace_id():
    """生成链路追踪 ID"""
    return f"tr_{uuid.uuid4().hex[:8]}"


def success_response(data, status_code=200):
    """成功响应"""
    return jsonify({"traceId": _trace_id(), "data": data}), status_code


def error_response(code, message, status_code, details=None):
    """错误响应"""
    return jsonify({
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "traceId": _trace_id()
        }
    }), status_code
