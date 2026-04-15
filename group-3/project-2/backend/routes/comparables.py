"""可比公司推荐、确认、查询接口"""
import os
from flask import Blueprint, request
from utils.response import success_response, error_response
from utils.data_store import read_json, write_json
from utils.validators import validate_company_exists
from services.ai_recommend import recommend_comparables
import config

comparables_bp = Blueprint("comparables", __name__)


@comparables_bp.route("/companies/<company_id>/comparables/recommend", methods=["POST"])
@validate_company_exists
def ai_recommend(company_id):
    """POST /companies/<id>/comparables/recommend — AI 推荐可比公司
    立即返回本地算法推荐结果（毫秒级），后台异步调用 AI 增强。
    前端可通过 GET /comparables/recommend 轮询获取 AI 增强结果。
    """
    result = recommend_comparables(company_id)
    if result is None:
        return error_response("AI_UNAVAILABLE", "AI 推荐服务不可用", 500)

    # 为默认推荐结果附加财务指标明细
    listed = read_json(os.path.join(config.DATA_DIR, "listed_companies.json"))
    listed_map = {lc["comparable_id"]: lc for lc in listed}

    for rec in result.get("recommendations", []):
        if "stock_price" not in rec:
            lc = listed_map.get(rec.get("comparable_id"))
            if lc:
                rec["stock_price"] = lc["stock_price"]
                rec["pe"] = lc["pe"]
                rec["pb"] = lc["pb"]
                rec["net_profit"] = lc["net_profit"]
                rec["net_assets"] = lc["net_assets"]
                rec["revenue"] = lc["revenue"]
                rec["market_cap"] = lc.get("market_cap", 0)

    return success_response(result)


@comparables_bp.route("/companies/<company_id>/comparables/recommend", methods=["GET"])
@validate_company_exists
def get_ai_recommend(company_id):
    """GET /companies/<id>/comparables/recommend — 查询 AI 增强的推荐结果
    前端可轮询此接口，当 ai_enhanced=true 时表示 AI 推荐已完成。
    """
    cache_path = os.path.join(config.DATA_DIR, "recommend_cache.json")
    cache = read_json(cache_path)
    if isinstance(cache, dict) and company_id in cache:
        return success_response(cache[company_id])

    return success_response({"company_id": company_id, "ai_enhanced": False, "recommendations": []})


@comparables_bp.route("/companies/<company_id>/comparables", methods=["PUT"])
@validate_company_exists
def confirm_comparables(company_id):
    """PUT /companies/<id>/comparables — 确认可比公司列表"""
    body = request.get_json(silent=True) or {}
    comparable_ids = body.get("comparable_ids", [])

    if not isinstance(comparable_ids, list) or len(comparable_ids) < 1 or len(comparable_ids) > 10:
        return error_response("INVALID_PARAMS", "comparable_ids 数组长度须为 1~10", 400,
                              {"field": "comparable_ids", "range": "1~10"})

    filepath = os.path.join(config.DATA_DIR, "comparables.json")
    all_comp = read_json(filepath)
    if not isinstance(all_comp, dict):
        all_comp = {}

    all_comp[company_id] = comparable_ids
    write_json(filepath, all_comp)

    return success_response({
        "company_id": company_id,
        "confirmed_count": len(comparable_ids),
        "comparable_ids": comparable_ids
    })


@comparables_bp.route("/companies/<company_id>/comparables", methods=["GET"])
@validate_company_exists
def get_comparables(company_id):
    """GET /companies/<id>/comparables — 已确认可比公司及指标"""
    all_comp = read_json(os.path.join(config.DATA_DIR, "comparables.json"))
    if not isinstance(all_comp, dict):
        all_comp = {}

    comp_ids = all_comp.get(company_id, [])
    listed = read_json(os.path.join(config.DATA_DIR, "listed_companies.json"))
    listed_map = {lc["comparable_id"]: lc for lc in listed}

    comparables = []
    for cid in comp_ids:
        lc = listed_map.get(cid)
        if lc:
            comparables.append({
                "comparable_id": lc["comparable_id"],
                "name": lc["name"],
                "industry": lc["industry"],
                "stock_price": lc["stock_price"],
                "pe": lc["pe"],
                "pb": lc["pb"],
                "net_profit": lc["net_profit"],
                "net_assets": lc["net_assets"],
                "revenue": lc["revenue"]
            })

    return success_response({
        "company_id": company_id,
        "comparables": comparables
    })
