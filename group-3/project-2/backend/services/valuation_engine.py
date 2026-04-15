"""估值计算引擎 — PE可比法、DCF现金流折现法、PB市净率法"""
import statistics


def compute_pe_valuation(target_net_profit, comparables):
    """PE 可比法估值"""
    pe_values = [c["pe"] for c in comparables if c.get("pe") and c["pe"] > 0]
    if not pe_values:
        return None

    pe_median = round(statistics.median(pe_values), 2)
    pe_min = min(pe_values)
    pe_max = max(pe_values)

    val_mid = round(pe_median * target_net_profit)
    val_low = round(pe_min * target_net_profit)
    val_high = round(pe_max * target_net_profit)

    return {
        "method_name": "pe_comparable",
        "display_name": "PE 可比法",
        "valuation_low": val_low,
        "valuation_mid": val_mid,
        "valuation_high": val_high,
        "params": {
            "comparable_pe_median": pe_median,
            "comparable_pe_range": [round(pe_min, 2), round(pe_max, 2)],
            "comparable_companies": [c["name"] for c in comparables]
        },
        "calculation_detail": (
            f"取{len(comparables)}家可比公司PE中位数{pe_median}，"
            f"乘以目标公司净利润{target_net_profit:,.0f}万元，"
            f"得估值{val_mid:,.0f}万元"
        )
    }


def compute_dcf_valuation(base_cashflow, discount_rate, growth_rate, projection_years):
    """DCF 现金流折现法"""
    yearly_cashflows = []
    total_pv = 0
    current_year = 2026  # 预测起始年

    for i in range(1, projection_years + 1):
        projected = base_cashflow * ((1 + growth_rate) ** i)
        discounted = projected / ((1 + discount_rate) ** i)
        yearly_cashflows.append({
            "year": f"{current_year + i - 1}E",
            "projected": round(projected),
            "discounted": round(discounted)
        })
        total_pv += discounted

    # 终值 = 最后一年现金流 * (1 + g) / (r - g)
    last_cf = base_cashflow * ((1 + growth_rate) ** projection_years)
    terminal_value = last_cf * (1 + growth_rate) / (discount_rate - growth_rate) if discount_rate > growth_rate else 0
    terminal_value_discounted = terminal_value / ((1 + discount_rate) ** projection_years)

    val_mid = round(total_pv + terminal_value_discounted)

    # 估值区间：±20%
    val_low = round(val_mid * 0.8)
    val_high = round(val_mid * 1.2)

    dcf_projection = {
        "base_cashflow": base_cashflow,
        "discount_rate": discount_rate,
        "growth_rate": growth_rate,
        "projection_years": projection_years,
        "yearly_cashflows": yearly_cashflows,
        "terminal_value": round(terminal_value),
        "terminal_value_discounted": round(terminal_value_discounted)
    }

    return {
        "method_name": "dcf",
        "display_name": "DCF 现金流折现法",
        "valuation_low": val_low,
        "valuation_mid": val_mid,
        "valuation_high": val_high,
        "params": {
            "discount_rate": discount_rate,
            "growth_rate": growth_rate,
            "projection_years": projection_years,
            "base_cashflow": base_cashflow
        },
        "calculation_detail": (
            f"基于经营现金流{base_cashflow:,.0f}万元，"
            f"{projection_years}年预测期，折现率{discount_rate*100:.0f}%，"
            f"永续增长率{growth_rate*100:.0f}%"
        ),
        "dcf_projection": dcf_projection
    }


def compute_pb_valuation(target_net_assets, comparables):
    """PB 市净率法估值"""
    pb_values = [c["pb"] for c in comparables if c.get("pb") and c["pb"] > 0]
    if not pb_values:
        return None

    pb_median = round(statistics.median(pb_values), 2)
    pb_min = min(pb_values)
    pb_max = max(pb_values)

    val_mid = round(pb_median * target_net_assets)
    val_low = round(pb_min * target_net_assets)
    val_high = round(pb_max * target_net_assets)

    return {
        "method_name": "pb",
        "display_name": "P/B 市净率法",
        "valuation_low": val_low,
        "valuation_mid": val_mid,
        "valuation_high": val_high,
        "params": {
            "comparable_pb_median": pb_median,
            "comparable_pb_range": [round(pb_min, 2), round(pb_max, 2)]
        },
        "calculation_detail": (
            f"取可比公司PB中位数{pb_median}，"
            f"乘以目标公司净资产{target_net_assets:,.0f}万元，"
            f"得估值{val_mid:,.0f}万元"
        )
    }


def compute_sensitivity(base_cashflow, projection_years):
    """敏感性分析：折现率 x 增长率矩阵"""
    discount_rates = [0.08, 0.09, 0.10, 0.11, 0.12, 0.13, 0.14]
    growth_rates = [0.03, 0.05, 0.07]

    scenarios = []
    for g in growth_rates:
        valuations = []
        for r in discount_rates:
            # 简化 DCF 计算
            total_pv = 0
            for i in range(1, projection_years + 1):
                cf = base_cashflow * ((1 + g) ** i)
                total_pv += cf / ((1 + r) ** i)

            last_cf = base_cashflow * ((1 + g) ** projection_years)
            tv = last_cf * (1 + g) / (r - g) if r > g else 0
            tv_pv = tv / ((1 + r) ** projection_years)
            total = total_pv + tv_pv
            # 转为万亿
            valuations.append(round(total / 10000000, 2))

        scenarios.append({
            "growth_rate": round(g * 100),
            "valuations": valuations
        })

    return {
        "discount_rates": [round(r * 100) for r in discount_rates],
        "scenarios": scenarios
    }
