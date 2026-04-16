"""pytest fixtures — Flask test client、测试数据、数据清理"""
import json
import os
import shutil
import sys
import tempfile

import pytest

# 确保 backend 目录在 sys.path 中
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import config  # noqa: E402


# ────────────────────────── 种子数据 ──────────────────────────

SEED_COMPANIES = [
    {"company_id": "comp_001", "name": "字节跳动", "industry": "互联网",
     "founded_year": 2012, "description": "全球领先的内容平台公司"},
    {"company_id": "comp_002", "name": "米哈游", "industry": "游戏",
     "founded_year": 2012, "description": "知名游戏研发公司"},
    {"company_id": "comp_003", "name": "蚂蚁集团", "industry": "金融科技",
     "founded_year": 2014, "description": "全球领先的金融科技开放平台"},
]

SEED_LISTED = [
    {"comparable_id": "listed_001", "name": "腾讯控股", "industry": "互联网",
     "stock_price": 498.6, "pe": 18.28, "pb": 3.59,
     "net_profit": 22401645, "net_assets": 114067428, "revenue": 55000000, "market_cap": 409502068},
    {"comparable_id": "listed_002", "name": "快手科技", "industry": "互联网",
     "stock_price": 45.7, "pe": 9.65, "pb": 2.28,
     "net_profit": 1559026, "net_assets": 6598511, "revenue": 11000000, "market_cap": 15044604},
    {"comparable_id": "listed_003", "name": "哔哩哔哩", "industry": "互联网",
     "stock_price": 194.8, "pe": 61.42, "pb": 4.71,
     "net_profit": 96173, "net_assets": 1254128, "revenue": 6500000, "market_cap": 5906945},
    {"comparable_id": "listed_004", "name": "Meta Platforms", "industry": "互联网",
     "stock_price": 662.49, "pe": 28.2, "pb": 7.71,
     "net_profit": 42786516, "net_assets": 156495427, "revenue": 134000000, "market_cap": 1206579743},
    {"comparable_id": "listed_005", "name": "阿里巴巴", "industry": "互联网",
     "stock_price": 128.9, "pe": 17.49, "pb": 2.14,
     "net_profit": 12691488, "net_assets": 103726228, "revenue": 86000000, "market_cap": 221974128},
]

SEED_FINANCIALS = [
    {"company_id": "comp_001", "period": "2025-FY",
     "revenue": 6000000, "net_profit": 1200000,
     "total_assets": 15000000, "net_assets": 8000000,
     "operating_cashflow": 1500000, "eps": None, "stock_price": None},
    {"company_id": "comp_001", "period": "2024-FY",
     "revenue": 5100000, "net_profit": 980000,
     "total_assets": 12800000, "net_assets": 6950000,
     "operating_cashflow": 1250000, "eps": None, "stock_price": None},
]

SAMPLE_FINANCIAL_DATA = {
    "period": "2025-FY",
    "revenue": 6000000,
    "net_profit": 1200000,
    "total_assets": 15000000,
    "net_assets": 8000000,
    "operating_cashflow": 1500000,
}


# ────────────────────────── Fixtures ──────────────────────────

@pytest.fixture()
def data_dir(tmp_path):
    """创建独立临时数据目录，写入种子数据"""
    d = tmp_path / "data"
    d.mkdir()
    _write(d / "companies.json", SEED_COMPANIES)
    _write(d / "listed_companies.json", SEED_LISTED)
    _write(d / "financials.json", SEED_FINANCIALS)
    _write(d / "comparables.json", {})
    _write(d / "valuations.json", {})
    return str(d)


@pytest.fixture()
def app(data_dir, monkeypatch):
    """创建 Flask 测试 app，数据目录指向临时目录"""
    monkeypatch.setattr(config, "DATA_DIR", data_dir)

    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    yield application


@pytest.fixture()
def client(app):
    """Flask test client"""
    return app.test_client()


@pytest.fixture()
def seeded_comparables(data_dir):
    """预设 comp_001 已确认 4 家可比公司"""
    comp = {"comp_001": ["listed_001", "listed_002", "listed_003", "listed_004"]}
    _write(os.path.join(data_dir, "comparables.json"), comp)
    return comp


@pytest.fixture()
def seeded_valuation(client, seeded_comparables):
    """预设 comp_001 已运行估值（通过 API 触发）"""
    resp = client.post(
        "/api/v1/valuation/companies/comp_001/valuations/run",
        json={},
        content_type="application/json",
    )
    assert resp.status_code == 200
    return resp.get_json()


# ────────────────────────── 辅助 ──────────────────────────

API = "/api/v1/valuation"


def _write(path, obj):
    with open(str(path), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
