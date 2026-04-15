"""数据同步服务 — 从腾讯财经 API 拉取上市公司实时行情数据

数据源: https://qt.gtimg.cn/q=<code>
- A 股: sh600036, sz000001
- 港股: hk00700
- 美股: usMAIN.META

策略:
1. 上市公司(listed_companies): 股价/PE/PB/市值 从腾讯财经实时拉取，
   净利润/净资产/营收 根据 市值/PE/PB 反算
2. 目标公司(companies): 非上市公司，保留静态数据
3. 财务数据(financials): 非上市公司财报无公开源，保留 Mock 数据
"""
import json
import os
import urllib.request
import urllib.error
from datetime import datetime

import config
from utils.data_store import read_json, write_json

# ========================
# 上市公司 → 股票代码映射
# ========================
LISTED_STOCK_MAP = {
    "listed_001": {"name": "腾讯控股",       "code": "hk00700",       "industry": "互联网"},
    "listed_002": {"name": "快手科技",       "code": "hk01024",       "industry": "互联网"},
    "listed_003": {"name": "哔哩哔哩",       "code": "hk09626",       "industry": "互联网"},
    "listed_004": {"name": "Meta Platforms", "code": "usMETA",          "industry": "互联网"},
    "listed_005": {"name": "阿里巴巴",       "code": "hk09988",       "industry": "互联网"},
    "listed_006": {"name": "美团",           "code": "hk03690",       "industry": "互联网"},
    "listed_007": {"name": "网易",           "code": "hk09999",       "industry": "游戏"},
    "listed_008": {"name": "拼多多",         "code": "usPDD",          "industry": "电商"},
    "listed_009": {"name": "京东",           "code": "hk09618",       "industry": "电商"},
    "listed_010": {"name": "中国平安",       "code": "sh601318",      "industry": "金融科技"},
    "listed_011": {"name": "招商银行",       "code": "sh600036",      "industry": "金融科技"},
}

# A 股字段索引（qt.gtimg.cn 返回的 ~ 分隔字段）
# 注意: index 38 是换手率，不是 PE
A_FIELDS = {
    "name": 1,
    "code": 2,
    "price": 3,
    "prev_close": 4,
    "pe": 39,              # 市盈率 (动态)
    "circ_market_cap": 44, # 流通市值 (亿元)
    "total_market_cap": 45,# 总市值 (亿元)
    "pb": 46,              # 市净率
}

# 港股字段索引
HK_FIELDS = {
    "name": 1,
    "code": 2,
    "price": 3,
    "prev_close": 4,
    "pe": 39,              # 市盈率
    "pb": 58,              # 市净率 (注意: 57是PE重复，58才是PB)
    "total_market_cap": 44,# 总市值 (亿港元)
}

# 美股字段索引
US_FIELDS = {
    "name": 1,
    "code": 2,
    "price": 3,
    "prev_close": 4,
    "pe": 39,              # 市盈率
    "pb": 51,              # 市净率 (美股PB在51位)
    "total_market_cap": 45,# 总市值 (亿美元) — 44是流通市值，45是总市值
}


def _fetch_quotes(codes):
    """批量获取实时行情

    Args:
        codes: list of stock codes, e.g. ["hk00700", "sh601318"]

    Returns:
        dict: {code: {field_name: value}}
    """
    query = ",".join(codes)
    url = f"https://qt.gtimg.cn/q={query}"

    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://finance.qq.com"
        })
        # 不使用代理
        proxy_handler = urllib.request.ProxyHandler({})
        opener = urllib.request.build_opener(proxy_handler)
        resp = opener.open(req, timeout=15)
        data = resp.read().decode("gbk", errors="replace")
    except Exception as e:
        print(f"[DataSync] 获取行情失败: {e}")
        return {}

    results = {}
    for segment in data.strip().split(";"):
        segment = segment.strip()
        if not segment or "=" not in segment:
            continue
        key, val = segment.split("=", 1)
        val = val.strip('"')
        fields = val.split("~")

        # 从 key 中提取代码，如 v_hk00700 → hk00700
        code = key.replace("v_", "").strip()

        # 判断市场
        if code.startswith("hk"):
            field_map = HK_FIELDS
        elif code.startswith("us"):
            field_map = US_FIELDS
        else:
            field_map = A_FIELDS

        parsed = {"_raw_fields_count": len(fields)}
        for fname, idx in field_map.items():
            if idx < len(fields):
                raw_val = fields[idx]
                # 尝试转为数字
                try:
                    parsed[fname] = float(raw_val) if raw_val and raw_val != "" else None
                except (ValueError, TypeError):
                    parsed[fname] = raw_val
            else:
                parsed[fname] = None

        results[code] = parsed

    return results


def _safe_float(val, default=0):
    """安全转浮点数"""
    if val is None:
        return default
    try:
        v = float(val)
        return v if v > 0 else default
    except (ValueError, TypeError):
        return default


def sync_listed_companies():
    """同步上市公司数据（实时行情 + 派生财务指标）

    Returns:
        tuple: (updated_count, total_count, error_messages)
    """
    filepath = os.path.join(config.DATA_DIR, "listed_companies.json")
    existing = read_json(filepath)
    existing_map = {c["comparable_id"]: c for c in existing} if isinstance(existing, list) else {}

    # 批量获取行情
    codes = [info["code"] for info in LISTED_STOCK_MAP.values()]
    quotes = _fetch_quotes(codes)

    if not quotes:
        return 0, len(LISTED_STOCK_MAP), ["无法获取行情数据，保留原有数据"]

    updated = []
    errors = []
    update_count = 0

    for comp_id, info in LISTED_STOCK_MAP.items():
        code = info["code"]
        quote = quotes.get(code)
        old = existing_map.get(comp_id, {})

        if quote is None:
            # 该股票无数据，保留旧值
            if old:
                updated.append(old)
            else:
                updated.append(_default_listed(comp_id, info))
            errors.append(f"{info['name']}({code}): 无行情数据")
            continue

        price = _safe_float(quote.get("price"))
        pe = _safe_float(quote.get("pe"))
        pb = _safe_float(quote.get("pb"))
        market_cap_raw = _safe_float(quote.get("total_market_cap"))

        # 腾讯行情市值单位：统一为 "亿" (亿元/亿港元/亿美元)
        # 转为万元人民币: 亿 * 10000 = 万
        if code.startswith("sh") or code.startswith("sz"):
            # A 股: 亿元 → 万元
            market_cap = round(market_cap_raw * 10000) if market_cap_raw > 0 else old.get("market_cap", 0)
        elif code.startswith("hk"):
            # 港股: 亿港元 → 万港元 → 万人民币 (×0.9)
            market_cap = round(market_cap_raw * 10000 * 0.9) if market_cap_raw > 0 else old.get("market_cap", 0)
        else:
            # 美股: 亿美元 → 万美元 → 万人民币 (×7.2)
            market_cap = round(market_cap_raw * 10000 * 7.2) if market_cap_raw > 0 else old.get("market_cap", 0)

        # 反算财务指标
        # net_profit = market_cap / PE (万元)
        net_profit = round(market_cap / pe) if pe > 0 else old.get("net_profit", 0)
        # net_assets = market_cap / PB (万元)
        net_assets = round(market_cap / pb) if pb > 0 else old.get("net_assets", 0)
        # revenue：无法从行情直接获取，保留旧值或用 net_profit * 估算倍数
        revenue = old.get("revenue", round(net_profit * 5)) if net_profit > 0 else old.get("revenue", 0)

        record = {
            "comparable_id": comp_id,
            "name": info["name"],
            "industry": info["industry"],
            "stock_price": round(price, 2) if price > 0 else old.get("stock_price", 0),
            "pe": round(pe, 2) if pe > 0 else old.get("pe", 0),
            "pb": round(pb, 2) if pb > 0 else old.get("pb", 0),
            "net_profit": net_profit,
            "net_assets": net_assets,
            "revenue": revenue,
            "market_cap": market_cap
        }
        updated.append(record)
        update_count += 1

    write_json(filepath, updated)
    return update_count, len(LISTED_STOCK_MAP), errors


def _default_listed(comp_id, info):
    """生成默认的上市公司记录（无法获取数据时使用）"""
    return {
        "comparable_id": comp_id,
        "name": info["name"],
        "industry": info["industry"],
        "stock_price": 0,
        "pe": 0,
        "pb": 0,
        "net_profit": 0,
        "net_assets": 0,
        "revenue": 0,
        "market_cap": 0
    }


def sync_all():
    """执行全量数据同步

    Returns:
        dict: 同步结果摘要
    """
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[DataSync] {ts} 开始同步数据...")

    updated, total, errors = sync_listed_companies()

    result = {
        "timestamp": ts,
        "listed_companies": {
            "updated": updated,
            "total": total,
            "errors": errors
        }
    }

    if errors:
        for e in errors:
            print(f"[DataSync] 警告: {e}")

    print(f"[DataSync] 同步完成: 上市公司 {updated}/{total} 条更新")
    return result


def debug_fields(code="hk00700"):
    """调试工具：打印指定股票代码的全部字段，用于验证字段索引

    用法: python -c "from services.data_sync import debug_fields; debug_fields('hk00700')"
    """
    url = f"https://qt.gtimg.cn/q={code}"
    proxy_handler = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(proxy_handler)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    resp = opener.open(req, timeout=15)
    data = resp.read().decode("gbk", errors="replace")

    for segment in data.strip().split(";"):
        segment = segment.strip()
        if not segment or "=" not in segment:
            continue
        key, val = segment.split("=", 1)
        val = val.strip('"')
        fields = val.split("~")
        print(f"\n{key} ({len(fields)} fields):")
        for i, v in enumerate(fields):
            print(f"  [{i:02d}] {v}")


if __name__ == "__main__":
    # 直接运行时执行同步
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    result = sync_all()
    print(json.dumps(result, ensure_ascii=False, indent=2))
