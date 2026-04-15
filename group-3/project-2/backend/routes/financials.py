"""财务数据导入与查询接口"""
import os
from flask import Blueprint, request
from utils.response import success_response, error_response
from utils.data_store import read_json, write_json
from utils.validators import validate_company_exists, validate_required_fields
import config

financials_bp = Blueprint("financials", __name__)

REQUIRED_FINANCIAL_FIELDS = ["period", "revenue", "net_profit", "total_assets", "net_assets", "operating_cashflow"]
NUMERIC_FIELDS = ["revenue", "net_profit", "total_assets", "net_assets", "operating_cashflow"]


@financials_bp.route("/companies/<company_id>/financials", methods=["POST"])
@validate_company_exists
@validate_required_fields(REQUIRED_FINANCIAL_FIELDS)
def import_financials(company_id):
    """POST /companies/<id>/financials — 导入财务数据"""
    body = request.get_json()

    # 校验数值字段非负
    for field in NUMERIC_FIELDS:
        val = body.get(field)
        if val is not None and (not isinstance(val, (int, float)) or val < 0):
            return error_response(
                "INVALID_FINANCIAL_DATA", f"{field} 必须为非负数值", 400,
                {"field": field}
            )

    filepath = os.path.join(config.DATA_DIR, "financials.json")
    all_fin = read_json(filepath)

    record = {
        "company_id": company_id,
        "period": body["period"],
        "revenue": body["revenue"],
        "net_profit": body["net_profit"],
        "total_assets": body["total_assets"],
        "net_assets": body["net_assets"],
        "operating_cashflow": body["operating_cashflow"],
        "eps": body.get("eps"),
        "stock_price": body.get("stock_price")
    }

    # 如果同公司同期已存在则更新
    updated = False
    for i, f in enumerate(all_fin):
        if f["company_id"] == company_id and f["period"] == body["period"]:
            all_fin[i] = record
            updated = True
            break
    if not updated:
        all_fin.append(record)

    write_json(filepath, all_fin)

    fields_imported = sum(1 for k in ["revenue", "net_profit", "total_assets",
                                       "net_assets", "operating_cashflow", "eps", "stock_price"]
                         if body.get(k) is not None)

    return success_response({
        "message": "财务数据导入成功",
        "company_id": company_id,
        "period": body["period"],
        "fields_imported": fields_imported
    }, 201)


@financials_bp.route("/companies/<company_id>/financials", methods=["GET"])
@validate_company_exists
def get_financials(company_id):
    """GET /companies/<id>/financials — 财务时序数据与财务比率"""
    all_fin = read_json(os.path.join(config.DATA_DIR, "financials.json"))
    company_fin = [f for f in all_fin if f["company_id"] == company_id]
    company_fin.sort(key=lambda x: x["period"], reverse=True)

    if not company_fin:
        return success_response({
            "company_id": company_id,
            "latest_summary": None,
            "financials": [],
            "ratios": {},
            "industry_avg_ratios": {}
        })

    latest = company_fin[0]
    prev = company_fin[1] if len(company_fin) > 1 else None

    # 同比计算
    def yoy(curr, prev_val):
        if prev_val and abs(prev_val) > 0:
            return round((curr - prev_val) / abs(prev_val) * 100, 1)
        return 0

    latest_summary = {
        "period": latest["period"],
        "revenue": latest["revenue"],
        "net_profit": latest["net_profit"],
        "total_assets": latest["total_assets"],
        "net_assets": latest["net_assets"],
        "operating_cashflow": latest["operating_cashflow"],
        "yoy_revenue": yoy(latest["revenue"], prev["revenue"]) if prev else 0,
        "yoy_net_profit": yoy(latest["net_profit"], prev["net_profit"]) if prev else 0,
        "yoy_net_assets": yoy(latest["net_assets"], prev["net_assets"]) if prev else 0,
        "summary_note": _summary_note(latest, prev)
    }

    # 关键财务比率
    ratios = _compute_ratios(latest, prev)

    # 行业平均比率（模拟）
    industry_avg_ratios = {
        "net_profit_margin": 15.0,
        "roa": 6.0,
        "revenue_growth": 12.0,
        "cashflow_ratio": 20.0,
        "debt_ratio": 52.0
    }

    return success_response({
        "company_id": company_id,
        "latest_summary": latest_summary,
        "financials": company_fin,
        "ratios": ratios,
        "industry_avg_ratios": industry_avg_ratios
    })


def _compute_ratios(latest, prev):
    """计算关键财务比率"""
    revenue = latest["revenue"] or 1
    total_assets = latest["total_assets"] or 1

    net_profit_margin = round(latest["net_profit"] / revenue * 100, 1)
    roa = round(latest["net_profit"] / total_assets * 100, 1)

    revenue_growth = 0
    if prev and prev["revenue"] and abs(prev["revenue"]) > 0:
        revenue_growth = round((latest["revenue"] - prev["revenue"]) / abs(prev["revenue"]) * 100, 1)

    cashflow_ratio = round(latest["operating_cashflow"] / revenue * 100, 1)
    debt_ratio = round((total_assets - latest["net_assets"]) / total_assets * 100, 1)

    return {
        "net_profit_margin": net_profit_margin,
        "roa": roa,
        "revenue_growth": revenue_growth,
        "cashflow_ratio": cashflow_ratio,
        "debt_ratio": debt_ratio
    }


def _summary_note(latest, prev):
    """生成摘要说明"""
    if not prev:
        return "首期数据"
    growth = (latest["revenue"] - prev["revenue"]) / abs(prev["revenue"]) * 100 if prev["revenue"] else 0
    if growth > 20:
        return "高速增长"
    elif growth > 10:
        return "稳健增长"
    elif growth > 0:
        return "温和增长"
    else:
        return "营收下滑"
