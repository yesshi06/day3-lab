"""估值计算、方法详情、综合摘要接口"""
import os
from datetime import datetime
from flask import Blueprint, request
from utils.response import success_response, error_response
from utils.data_store import read_json, write_json
from utils.validators import validate_company_exists
from services.valuation_engine import (
    compute_pe_valuation, compute_dcf_valuation,
    compute_pb_valuation, compute_sensitivity
)
from services.ai_recommend import generate_ai_recommendation, async_generate_ai_recommendation
import config

valuations_bp = Blueprint("valuations", __name__)


def _format_wan_yi(value):
    """格式化万元为万亿/亿元显示"""
    if value >= 10000000:
        return f"{value / 10000000:.1f}万亿"
    elif value >= 10000:
        return f"{value / 10000:.0f}亿"
    else:
        return f"{value}万"


@valuations_bp.route("/companies/<company_id>/valuations/run", methods=["POST"])
@validate_company_exists
def run_valuation(company_id):
    """POST /companies/<id>/valuations/run — 运行估值计算"""
    # 前置校验：必须已确认可比公司
    all_comp = read_json(os.path.join(config.DATA_DIR, "comparables.json"))
    if not isinstance(all_comp, dict):
        all_comp = {}
    comp_ids = all_comp.get(company_id, [])
    if not comp_ids:
        return error_response("NO_COMPARABLES", "未确认可比公司即发起估值计算", 400)

    # 解析 DCF 参数
    body = request.get_json(silent=True) or {}
    discount_rate = body.get("dcf_discount_rate", config.DCF_DEFAULT_DISCOUNT_RATE)
    growth_rate = body.get("dcf_growth_rate", config.DCF_DEFAULT_GROWTH_RATE)
    projection_years = body.get("dcf_projection_years", config.DCF_DEFAULT_PROJECTION_YEARS)

    # DCF 参数校验
    if not (0.01 <= discount_rate <= 0.30):
        return error_response("INVALID_PARAMS", "折现率超出范围", 400,
                              {"field": "dcf_discount_rate", "range": "0.01~0.30"})
    if not (0 <= growth_rate <= 0.15):
        return error_response("INVALID_PARAMS", "永续增长率超出范围", 400,
                              {"field": "dcf_growth_rate", "range": "0~0.15"})
    if not (3 <= projection_years <= 10):
        return error_response("INVALID_PARAMS", "预测年数超出范围", 400,
                              {"field": "dcf_projection_years", "range": "3~10"})

    # 获取可比公司指标
    listed = read_json(os.path.join(config.DATA_DIR, "listed_companies.json"))
    listed_map = {lc["comparable_id"]: lc for lc in listed}
    comparables = [listed_map[cid] for cid in comp_ids if cid in listed_map]

    # 获取目标公司最新财务数据
    all_fin = read_json(os.path.join(config.DATA_DIR, "financials.json"))
    company_fin = [f for f in all_fin if f["company_id"] == company_id]
    company_fin.sort(key=lambda x: x["period"], reverse=True)

    if not company_fin:
        return error_response("INVALID_FINANCIAL_DATA", "目标公司无财务数据", 400)

    latest = company_fin[0]
    target_net_profit = latest["net_profit"]
    target_net_assets = latest["net_assets"]
    base_cashflow = latest["operating_cashflow"]

    # 计算三种估值
    methods = []
    dcf_projection = None

    pe_result = compute_pe_valuation(target_net_profit, comparables)
    if pe_result:
        methods.append(pe_result)

    dcf_result = compute_dcf_valuation(base_cashflow, discount_rate, growth_rate, projection_years)
    if dcf_result:
        dcf_projection = dcf_result.pop("dcf_projection", None)
        methods.append(dcf_result)

    pb_result = compute_pb_valuation(target_net_assets, comparables)
    if pb_result:
        methods.append(pb_result)

    # 保存估值结果
    filepath = os.path.join(config.DATA_DIR, "valuations.json")
    all_val = read_json(filepath)
    if not isinstance(all_val, dict):
        all_val = {}

    # 获取公司名称
    companies = read_json(os.path.join(config.DATA_DIR, "companies.json"))
    company = next((c for c in companies if c["company_id"] == company_id), {})

    # 提取各方法中位数
    pe_mid = dcf_mid = pb_mid = 0
    for m in methods:
        if m["method_name"] == "pe_comparable":
            pe_mid = m["valuation_mid"]
        elif m["method_name"] == "dcf":
            dcf_mid = m["valuation_mid"]
        elif m["method_name"] == "pb":
            pb_mid = m["valuation_mid"]

    # 立即生成默认 AI 推荐（本地计算，毫秒级）
    ai_recommendation = generate_ai_recommendation({
        "company_name": company.get("name", ""),
        "pe_mid": pe_mid,
        "dcf_mid": dcf_mid,
        "pb_mid": pb_mid,
        "comparable_count": len(comparables)
    })

    # 预计算敏感性分析
    sensitivity = compute_sensitivity(base_cashflow, projection_years)

    all_val[company_id] = {
        "company_name": company.get("name", ""),
        "last_valued_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "target_net_profit": target_net_profit,
        "target_net_assets": target_net_assets,
        "base_cashflow": base_cashflow,
        "comparable_count": len(comparables),
        "methods": methods,
        "dcf_projection": dcf_projection,
        "comparable_scatter": [
            {"name": c["name"], "pe": c["pe"], "pb": c["pb"], "revenue": c["revenue"]}
            for c in comparables
        ],
        "dcf_params": {
            "discount_rate": discount_rate,
            "growth_rate": growth_rate,
            "projection_years": projection_years
        },
        "ai_recommendation": ai_recommendation,
        "sensitivity_analysis": sensitivity
    }

    write_json(filepath, all_val)

    # 异步调用 AI 生成更优质的估值推荐（完成后自动回写 valuations.json）
    async_generate_ai_recommendation(company_id, {
        "company_name": company.get("name", ""),
        "pe_mid": pe_mid,
        "dcf_mid": dcf_mid,
        "pb_mid": pb_mid,
        "comparable_count": len(comparables)
    })

    return success_response({
        "company_id": company_id,
        "methods_computed": len(methods),
        "methods": [m["method_name"] for m in methods],
        "message": "估值计算完成，请查看详情"
    })


@valuations_bp.route("/companies/<company_id>/valuations/methods", methods=["GET"])
@validate_company_exists
def get_valuation_methods(company_id):
    """GET /companies/<id>/valuations/methods — 各方法估值详情与图表数据"""
    all_val = read_json(os.path.join(config.DATA_DIR, "valuations.json"))
    if not isinstance(all_val, dict):
        all_val = {}

    val_data = all_val.get(company_id)
    if not val_data:
        return error_response("VALUATION_NOT_FOUND", "尚未生成估值结果", 404,
                              {"company_id": company_id})

    return success_response({
        "company_id": company_id,
        "company_name": val_data["company_name"],
        "target_net_profit": val_data["target_net_profit"],
        "target_net_assets": val_data["target_net_assets"],
        "comparable_count": val_data["comparable_count"],
        "methods": val_data["methods"],
        "dcf_projection": val_data.get("dcf_projection"),
        "comparable_scatter": val_data.get("comparable_scatter", [])
    })


@valuations_bp.route("/companies/<company_id>/valuations/summary", methods=["GET"])
@validate_company_exists
def get_valuation_summary(company_id):
    """GET /companies/<id>/valuations/summary — 估值结果综合摘要"""
    all_val = read_json(os.path.join(config.DATA_DIR, "valuations.json"))
    if not isinstance(all_val, dict):
        all_val = {}

    val_data = all_val.get(company_id)
    if not val_data:
        return error_response("VALUATION_NOT_FOUND", "尚未生成估值结果", 404,
                              {"company_id": company_id})

    methods = val_data["methods"]
    company_name = val_data["company_name"]

    # 加权估值中枢 PE 40% / DCF 35% / PB 25%
    weights = {"pe_comparable": config.WEIGHT_PE, "dcf": config.WEIGHT_DCF, "pb": config.WEIGHT_PB}
    total_weight = 0
    weighted_sum = 0
    all_lows = []
    all_highs = []

    methods_summary = []
    pe_mid = dcf_mid = pb_mid = 0

    for m in methods:
        w = weights.get(m["method_name"], 0)
        total_weight += w
        weighted_sum += m["valuation_mid"] * w
        all_lows.append(m["valuation_low"])
        all_highs.append(m["valuation_high"])

        if m["method_name"] == "pe_comparable":
            pe_mid = m["valuation_mid"]
        elif m["method_name"] == "dcf":
            dcf_mid = m["valuation_mid"]
        elif m["method_name"] == "pb":
            pb_mid = m["valuation_mid"]

        methods_summary.append({
            "method_name": m["method_name"],
            "display_name": m["display_name"],
            "valuation_low": m["valuation_low"],
            "valuation_mid": m["valuation_mid"],
            "valuation_high": m["valuation_high"],
            "valuation_range": f"{_format_wan_yi(m['valuation_low'])} ~ {_format_wan_yi(m['valuation_high'])}",
            "weight": w
        })

    valuation_center = round(weighted_sum / total_weight) if total_weight > 0 else 0
    valuation_range_low = min(all_lows) if all_lows else 0
    valuation_range_high = max(all_highs) if all_highs else 0

    # 直接读取预缓存的 AI 推荐和敏感性分析（在 POST /valuations/run 时已计算）
    ai_recommendation = val_data.get("ai_recommendation")
    if not ai_recommendation:
        # 兼容旧数据：若缓存中无 AI 推荐则实时生成
        ai_recommendation = generate_ai_recommendation({
            "company_name": company_name,
            "pe_mid": pe_mid,
            "dcf_mid": dcf_mid,
            "pb_mid": pb_mid,
            "comparable_count": val_data["comparable_count"]
        })

    sensitivity = val_data.get("sensitivity_analysis")
    if not sensitivity:
        dcf_params = val_data.get("dcf_params", {})
        sensitivity = compute_sensitivity(
            val_data["base_cashflow"],
            dcf_params.get("projection_years", config.DCF_DEFAULT_PROJECTION_YEARS)
        )

    # 各方法可信度评分
    confidence_scores = [
        {
            "method_name": "pe_comparable",
            "display_name": "PE 可比法",
            "data_quality": 90,
            "method_applicability": 85,
            "sample_sufficiency": min(95, val_data["comparable_count"] * 20)
        },
        {
            "method_name": "dcf",
            "display_name": "DCF 法",
            "data_quality": 75,
            "method_applicability": 80,
            "sample_sufficiency": 70
        },
        {
            "method_name": "pb",
            "display_name": "P/B 法",
            "data_quality": 70,
            "method_applicability": 60,
            "sample_sufficiency": min(90, val_data["comparable_count"] * 18)
        }
    ]

    return success_response({
        "company_id": company_id,
        "company_name": company_name,
        "valuation_center": valuation_center,
        "valuation_range_low": valuation_range_low,
        "valuation_range_high": valuation_range_high,
        "methods_summary": methods_summary,
        "ai_recommendation": ai_recommendation,
        "sensitivity_analysis": sensitivity,
        "confidence_scores": confidence_scores
    })
