"""统计聚合服务"""
import os
from collections import Counter
from utils.data_store import read_json
from utils.data_store import read_json
import config


def compute_statistics():
    """计算公司列表页统计与图表数据"""
    companies = read_json(os.path.join(config.DATA_DIR, "companies.json"))
    valuations = read_json(os.path.join(config.DATA_DIR, "valuations.json"))
    listed = read_json(os.path.join(config.DATA_DIR, "listed_companies.json"))

    if not isinstance(valuations, dict):
        valuations = {}

    total = len(companies)
    valued = sum(1 for c in companies if c["company_id"] in valuations)
    valued_ratio = round(valued / total * 100, 1) if total > 0 else 0

    # 行业分布
    industry_counter = Counter(c["industry"] for c in companies)
    industry_distribution = [
        {"industry": ind, "count": cnt}
        for ind, cnt in industry_counter.most_common()
    ]

    # 覆盖行业数
    total_industries = len(industry_counter)

    # 估值状态
    valuation_status = {
        "valued": valued,
        "not_valued": total - valued
    }

    # 各行业平均 PE（基于上市公司数据）
    industry_pe = {}
    for lc in listed:
        ind = lc["industry"]
        if ind not in industry_pe:
            industry_pe[ind] = []
        if lc.get("pe"):
            industry_pe[ind].append(lc["pe"])

    industry_avg_pe = []
    for ind, pes in industry_pe.items():
        if pes:
            industry_avg_pe.append({
                "industry": ind,
                "avg_pe": round(sum(pes) / len(pes), 1)
            })

    return {
        "total_companies": total,
        "valued_companies": valued,
        "valued_ratio": valued_ratio,
        "total_industries": total_industries,
        "weekly_new_companies": 2,
        "industry_distribution": industry_distribution,
        "valuation_status": valuation_status,
        "industry_avg_pe": industry_avg_pe
    }
