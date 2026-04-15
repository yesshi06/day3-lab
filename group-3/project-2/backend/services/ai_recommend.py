"""AI 推荐可比公司服务"""
import json
import os
import threading
import logging
import dashscope
from dashscope import Generation
from utils.data_store import read_json, write_json
import config

logger = logging.getLogger(__name__)


def recommend_comparables(company_id):
    """调用 DashScope AI 推荐可比公司"""
    companies = read_json(os.path.join(config.DATA_DIR, "companies.json"))
    listed = read_json(os.path.join(config.DATA_DIR, "listed_companies.json"))
    financials = read_json(os.path.join(config.DATA_DIR, "financials.json"))

    company = next((c for c in companies if c["company_id"] == company_id), None)
    if not company:
        return None

    # 获取最新财务数据
    comp_fin = [f for f in financials if f["company_id"] == company_id]
    comp_fin.sort(key=lambda x: x["period"], reverse=True)
    latest_fin = comp_fin[0] if comp_fin else {}

    # 过滤掉目标公司自身（避免自己跟自己比）
    target_name = company["name"]
    listed = [lc for lc in listed if lc["name"] != target_name]

    # 构造 prompt
    listed_names = [lc["name"] for lc in listed]
    prompt = (
        f"你是一位资深金融分析师。目标公司「{target_name}」，行业：{company['industry']}，"
        f"营收：{latest_fin.get('revenue', '未知')}万元，净利润：{latest_fin.get('net_profit', '未知')}万元。\n"
        f"可选的上市公司列表：{', '.join(listed_names)}。\n"
        f"请从中推荐4~6家最合适的可比公司，返回 JSON 数组，每项包含：\n"
        f"comparable_id（格式 listed_XXX）、name、industry、reason（推荐理由）、"
        f"similarity_score（0~1）、similarity_dimensions（包含 industry/scale/business_model/profitability/growth，各 0~100）。\n"
        f"仅返回 JSON 数组，不要其他内容。"
    )

    # 立即返回默认推荐（本地算法，毫秒级）
    result = _default_recommendations(company_id, company, listed)
    result["ai_enhanced"] = False

    # 异步调用 AI 增强推荐，完成后缓存到文件
    threading.Thread(
        target=_async_ai_recommend,
        args=(company_id, company, listed, target_name, prompt),
        daemon=True
    ).start()

    return result


def _async_ai_recommend(company_id, company, listed, target_name, prompt):
    """后台线程：调用 AI 并缓存推荐结果"""
    try:
        dashscope.api_key = config.DASHSCOPE_API_KEY
        response = Generation.call(
            model=config.DASHSCOPE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            result_format="message"
        )

        if response and response.output and response.output.choices:
            content = response.output.choices[0].message.content
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content
                content = content.rsplit("```", 1)[0]
            recommendations = json.loads(content)

            listed_map = {lc["name"]: lc for lc in listed}
            valid_recs = []
            for rec in recommendations:
                name = rec.get("name", "")
                if name in listed_map and name != target_name:
                    lc = listed_map[name]
                    rec["comparable_id"] = lc["comparable_id"]
                    rec["industry"] = lc["industry"]
                    dims = rec.get("similarity_dimensions", {})
                    rec["similarity_dimensions"] = {
                        "industry": dims.get("industry", 70),
                        "scale": dims.get("scale", 60),
                        "business_model": dims.get("business_model", 65),
                        "profitability": dims.get("profitability", 60),
                        "growth": dims.get("growth", 55)
                    }
                    # 附加财务指标
                    rec["stock_price"] = lc["stock_price"]
                    rec["pe"] = lc["pe"]
                    rec["pb"] = lc["pb"]
                    rec["net_profit"] = lc["net_profit"]
                    rec["net_assets"] = lc["net_assets"]
                    rec["revenue"] = lc["revenue"]
                    rec["market_cap"] = lc.get("market_cap", 0)
                    valid_recs.append(rec)

            if valid_recs:
                ai_result = {
                    "company_id": company_id,
                    "ai_enhanced": True,
                    "prompt_summary": f"基于{company['name']}的行业属性（{company['industry']}）、营收规模和业务模式，AI推荐以下{len(valid_recs)}家可比上市公司。",
                    "recommendations": valid_recs
                }
                # 缓存到文件
                cache_path = os.path.join(config.DATA_DIR, "recommend_cache.json")
                cache = read_json(cache_path)
                if not isinstance(cache, dict):
                    cache = {}
                cache[company_id] = ai_result
                write_json(cache_path, cache)
                logger.info(f"AI 推荐完成: {company['name']} -> {len(valid_recs)} 家可比公司")

    except Exception as e:
        logger.warning(f"AI 推荐失败: {company_id} - {e}")


def _default_recommendations(company_id, company, listed):
    """默认推荐逻辑"""
    # 过滤掉目标公司自身
    target_name = company["name"]
    listed = [lc for lc in listed if lc["name"] != target_name]
    # 优先同行业
    same_ind = [lc for lc in listed if lc["industry"] == company["industry"]]
    others = [lc for lc in listed if lc["industry"] != company["industry"]]
    candidates = (same_ind + others)[:5]

    recommendations = []
    for i, lc in enumerate(candidates):
        is_same = lc["industry"] == company["industry"]
        recommendations.append({
            "comparable_id": lc["comparable_id"],
            "name": lc["name"],
            "industry": lc["industry"],
            "reason": f"{'同行业' if is_same else '跨行业'}可比公司，具有相似业务模式",
            "similarity_score": round(0.92 - i * 0.04, 2),
            "similarity_dimensions": {
                "industry": 95 if is_same else 50,
                "scale": 75 - i * 5,
                "business_model": 85 if is_same else 60,
                "profitability": 70 + i * 3,
                "growth": 80 - i * 5
            }
        })

    return {
        "company_id": company_id,
        "prompt_summary": f"基于{company['name']}的行业属性（{company['industry']}）、营收规模和业务模式，推荐以下{len(recommendations)}家可比上市公司。",
        "recommendations": recommendations
    }


def generate_ai_recommendation(valuation_data):
    """生成估值推荐总结（立即返回默认结果，后台异步调用 AI）"""
    # 立即返回本地计算的默认推荐
    default_rec = _default_ai_recommendation(valuation_data)
    default_rec["ai_enhanced"] = False
    return default_rec


def async_generate_ai_recommendation(company_id, valuation_data):
    """异步调用 AI 生成估值推荐，完成后写入 valuations.json 缓存"""
    threading.Thread(
        target=_async_ai_valuation_recommend,
        args=(company_id, valuation_data),
        daemon=True
    ).start()


def _async_ai_valuation_recommend(company_id, valuation_data):
    """后台线程：调用 AI 并更新 valuations.json 中的 ai_recommendation"""
    try:
        dashscope.api_key = config.DASHSCOPE_API_KEY

        prompt = (
            f"你是一位资深金融分析师。以下是公司「{valuation_data['company_name']}」的估值分析结果：\n"
            f"PE可比法估值中位数：{valuation_data.get('pe_mid', 0)}万元\n"
            f"DCF法估值中位数：{valuation_data.get('dcf_mid', 0)}万元\n"
            f"PB法估值中位数：{valuation_data.get('pb_mid', 0)}万元\n"
            f"可比公司数量：{valuation_data.get('comparable_count', 0)}家\n\n"
            f"请给出估值推荐，返回 JSON 对象包含：recommended_method（推荐方法名称）、"
            f"reason（推荐理由，50字以内）、summary（综合说明，150字以内）、confidence（置信度0~100）。\n"
            f"仅返回 JSON 对象。"
        )

        response = Generation.call(
            model=config.DASHSCOPE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            result_format="message"
        )

        if response and response.output and response.output.choices:
            content = response.output.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content
                content = content.rsplit("```", 1)[0]
            result = json.loads(content)
            ai_rec = {
                "recommended_method": result.get("recommended_method", "PE可比法"),
                "reason": result.get("reason", "PE可比法适用于盈利稳定的成熟期公司"),
                "summary": result.get("summary", ""),
                "confidence": min(100, max(0, result.get("confidence", 75))),
                "ai_enhanced": True
            }

            # 回写 valuations.json
            filepath = os.path.join(config.DATA_DIR, "valuations.json")
            all_val = read_json(filepath)
            if isinstance(all_val, dict) and company_id in all_val:
                all_val[company_id]["ai_recommendation"] = ai_rec
                write_json(filepath, all_val)
                logger.info(f"AI 估值推荐完成: {valuation_data['company_name']}")

    except Exception as e:
        logger.warning(f"AI 估值推荐失败: {company_id} - {e}")


def _default_ai_recommendation(valuation_data):
    """默认 AI 推荐"""
    company_name = valuation_data.get("company_name", "目标公司")
    pe_mid = valuation_data.get("pe_mid", 0)
    dcf_mid = valuation_data.get("dcf_mid", 0)
    pb_mid = valuation_data.get("pb_mid", 0)

    return {
        "recommended_method": "PE可比法",
        "reason": "目标公司处于成熟期互联网行业，盈利稳定，PE可比法最能反映市场对该行业的估值共识",
        "summary": (
            f"综合三种估值方法，{company_name}估值中枢约"
            f"{_format_wan_yi(int((pe_mid * 0.4 + dcf_mid * 0.35 + pb_mid * 0.25)))}。"
            f"考虑到公司盈利能力稳定且可比公司样本充足，PE可比法最具参考价值。"
            f"DCF法受折现率假设影响较大，P/B法因轻资产属性偏高，建议以PE法为锚。"
        ),
        "confidence": 82
    }


def _format_wan_yi(value):
    """格式化万元为万亿/亿元显示"""
    if value >= 10000000:
        return f"{value / 10000000:.1f}万亿"
    elif value >= 10000:
        return f"{value / 10000:.0f}亿"
    else:
        return f"{value}万"
