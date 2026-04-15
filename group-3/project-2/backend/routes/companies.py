"""公司列表、统计、详情接口"""
import os
from flask import Blueprint, request
from utils.response import success_response, error_response
from utils.data_store import read_json
from utils.validators import validate_company_exists
from services.statistics import compute_statistics
import config

companies_bp = Blueprint("companies", __name__)


@companies_bp.route("/companies", methods=["GET"])
def get_companies():
    """GET /companies — 公司列表（搜索/筛选）"""
    keyword = request.args.get("keyword", "").strip()
    industry = request.args.get("industry", "").strip()
    page = request.args.get("page", config.DEFAULT_PAGE, type=int)
    page_size = request.args.get("page_size", config.DEFAULT_PAGE_SIZE, type=int)

    # 校验 page_size
    if page_size < 1 or page_size > config.MAX_PAGE_SIZE:
        return error_response("INVALID_PARAMS", "page_size 超出范围", 400,
                              {"field": "page_size", "range": "1~100"})

    companies = read_json(os.path.join(config.DATA_DIR, "companies.json"))
    valuations = read_json(os.path.join(config.DATA_DIR, "valuations.json"))
    if not isinstance(valuations, dict):
        valuations = {}

    # 筛选
    if keyword:
        companies = [c for c in companies if keyword.lower() in c["name"].lower()]
    if industry:
        companies = [c for c in companies if c["industry"] == industry]

    total = len(companies)

    # 分页
    start = (page - 1) * page_size
    end = start + page_size
    page_items = companies[start:end]

    result = []
    for c in page_items:
        cid = c["company_id"]
        val_data = valuations.get(cid)
        item = {
            "company_id": cid,
            "name": c["name"],
            "industry": c["industry"],
            "has_valuation": val_data is not None,
            "last_valued_at": val_data.get("last_valued_at") if val_data else None
        }
        result.append(item)

    return success_response({
        "total": total,
        "page": page,
        "page_size": page_size,
        "companies": result
    })


@companies_bp.route("/statistics", methods=["GET"])
def get_statistics():
    """GET /statistics — 公司列表页统计与图表数据"""
    data = compute_statistics()
    return success_response(data)


@companies_bp.route("/companies/<company_id>", methods=["GET"])
@validate_company_exists
def get_company_detail(company_id):
    """GET /companies/<id> — 公司详情与行业信息"""
    companies = read_json(os.path.join(config.DATA_DIR, "companies.json"))
    financials = read_json(os.path.join(config.DATA_DIR, "financials.json"))
    listed = read_json(os.path.join(config.DATA_DIR, "listed_companies.json"))

    company = next(c for c in companies if c["company_id"] == company_id)
    has_financials = any(f["company_id"] == company_id for f in financials)

    # 行业信息
    same_industry = [c for c in companies if c["industry"] == company["industry"]]
    same_listed = [lc for lc in listed if lc["industry"] == company["industry"]]

    # 行业平均 PE
    pe_values = [lc["pe"] for lc in same_listed if lc.get("pe")]
    avg_pe = round(sum(pe_values) / len(pe_values), 1) if pe_values else 0

    # PE 分布直方图
    pe_distribution = [
        {"range": "<15", "count": len([p for p in pe_values if p < 15])},
        {"range": "15-20", "count": len([p for p in pe_values if 15 <= p < 20])},
        {"range": "20-25", "count": len([p for p in pe_values if 20 <= p < 25])},
        {"range": "25-30", "count": len([p for p in pe_values if 25 <= p < 30])},
        {"range": "30-35", "count": len([p for p in pe_values if 30 <= p < 35])},
        {"range": ">35", "count": len([p for p in pe_values if p >= 35])},
    ]

    return success_response({
        "company_id": company["company_id"],
        "name": company["name"],
        "industry": company["industry"],
        "founded_year": company.get("founded_year"),
        "description": company.get("description"),
        "has_financials": has_financials,
        "industry_info": {
            "avg_pe": avg_pe,
            "growth_rate": 12.5,
            "company_count": len(same_industry) + len(same_listed),
            "pe_distribution": pe_distribution
        }
    })
