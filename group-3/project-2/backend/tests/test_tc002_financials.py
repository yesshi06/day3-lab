"""TC-002: 财务数据 API 测试（US-002）— 4 个 P0 用例
对齐 Spec 13-测试策略与质量门禁 §1.2
"""
import json
import os
import time

API = "/api/v1/valuation"


class TestTC002Financials:
    """US-002 财务数据"""

    # ── TC-002-01 ────────────────────────────────────────────
    def test_TC002_01_import_financial_data(self, client):
        """TC-002-01 导入财务数据
        前置: 公司存在
        步骤: POST /companies/comp_001/financials（完整数据）
        期望: 201，导入成功，包含三表字段
        """
        payload = {
            "period": "2026-Q1",
            "revenue": 7000000,
            "net_profit": 1400000,
            "total_assets": 16000000,
            "net_assets": 9000000,
            "operating_cashflow": 1700000,
        }
        start = time.time()
        resp = client.post(
            f"{API}/companies/comp_001/financials",
            json=payload,
            content_type="application/json",
        )
        elapsed = time.time() - start

        assert resp.status_code == 201
        data = resp.get_json()["data"]
        assert data["message"] == "财务数据导入成功"
        assert data["company_id"] == "comp_001"
        assert data["period"] == "2026-Q1"
        assert "fields_imported" in data
        # SLO: 财务导入 ≤ 2s
        assert elapsed <= 2.0, f"导入耗时 {elapsed:.3f}s 超过 2s SLO"

    # ── TC-002-02 ────────────────────────────────────────────
    def test_TC002_02_missing_required_field(self, client):
        """TC-002-02 缺少必填字段
        前置: 公司存在
        步骤: POST /financials（缺 revenue）
        期望: 400, INVALID_FINANCIAL_DATA
        """
        payload = {
            "period": "2026-Q1",
            # revenue 缺失
            "net_profit": 1400000,
            "total_assets": 16000000,
            "net_assets": 9000000,
            "operating_cashflow": 1700000,
        }
        resp = client.post(
            f"{API}/companies/comp_001/financials",
            json=payload,
            content_type="application/json",
        )
        assert resp.status_code == 400
        body = resp.get_json()
        assert body["error"]["code"] == "INVALID_FINANCIAL_DATA"
        assert "missing_fields" in body["error"]["details"]

    # ── TC-002-03 ────────────────────────────────────────────
    def test_TC002_03_get_financial_data(self, client):
        """TC-002-03 获取财务数据
        前置: 已导入
        步骤: GET /companies/comp_001/financials
        期望: 200，返回 financials 数组
        """
        resp = client.get(f"{API}/companies/comp_001/financials")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "financials" in data
        assert isinstance(data["financials"], list)
        assert len(data["financials"]) >= 1
        # 检查按期间降序排列
        periods = [f["period"] for f in data["financials"]]
        assert periods == sorted(periods, reverse=True)

    # ── TC-002-04 ────────────────────────────────────────────
    def test_TC002_04_duplicate_period_overwrite(self, client, data_dir):
        """TC-002-04 同期覆盖
        前置: 已有 2025-FY
        步骤: POST /financials period=2025-FY（新 revenue）
        期望: 201，旧数据被覆盖
        """
        new_revenue = 6500000
        payload = {
            "period": "2025-FY",
            "revenue": new_revenue,
            "net_profit": 1300000,
            "total_assets": 15500000,
            "net_assets": 8500000,
            "operating_cashflow": 1600000,
        }
        resp = client.post(
            f"{API}/companies/comp_001/financials",
            json=payload,
            content_type="application/json",
        )
        assert resp.status_code == 201

        # 验证覆盖后数据
        resp2 = client.get(f"{API}/companies/comp_001/financials")
        data = resp2.get_json()["data"]
        fy_records = [f for f in data["financials"] if f["period"] == "2025-FY"]
        assert len(fy_records) == 1, "同期数据应只保留一条"
        assert fy_records[0]["revenue"] == new_revenue, "revenue 应已被覆盖"
