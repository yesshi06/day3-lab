"""TC-003: 可比公司 API 测试（US-003）— 5 个 P0 用例
对齐 Spec 13-测试策略与质量门禁 §1.3
"""
import time
from unittest.mock import patch

API = "/api/v1/valuation"


class TestTC003Comparables:
    """US-003 可比公司"""

    # ── TC-003-01 ────────────────────────────────────────────
    def test_TC003_01_ai_recommend_comparables(self, client):
        """TC-003-01 AI 推荐可比公司
        前置: 目标公司有信息
        步骤: POST /comparables/recommend
        期望: 200，返回 4~6 家 + 相似度分数
        Mock AI 接口，使用默认推荐逻辑
        """
        start = time.time()
        resp = client.post(f"{API}/companies/comp_001/comparables/recommend")
        elapsed = time.time() - start

        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["company_id"] == "comp_001"
        recs = data["recommendations"]
        assert isinstance(recs, list)
        assert 4 <= len(recs) <= 6, f"推荐数量 {len(recs)} 不在 4~6 范围"
        for r in recs:
            assert "comparable_id" in r
            assert "name" in r
            assert "industry" in r
            assert "reason" in r
            assert "similarity_score" in r
            assert 0 <= r["similarity_score"] <= 1
        # SLO: AI 推荐 ≤ 10s
        assert elapsed <= 10.0, f"AI 推荐耗时 {elapsed:.3f}s 超过 10s SLO"

    # ── TC-003-02 ────────────────────────────────────────────
    def test_TC003_02_confirm_comparables(self, client):
        """TC-003-02 确认可比公司
        前置: 有推荐结果
        步骤: PUT /comparables, ids=[...]
        期望: 200, confirmed_count 正确
        """
        ids = ["listed_001", "listed_002", "listed_003"]
        resp = client.put(
            f"{API}/companies/comp_001/comparables",
            json={"comparable_ids": ids},
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["company_id"] == "comp_001"
        assert data["confirmed_count"] == len(ids)
        assert data["comparable_ids"] == ids

    # ── TC-003-03 ────────────────────────────────────────────
    def test_TC003_03_get_confirmed_comparables(self, client, seeded_comparables):
        """TC-003-03 获取已确认可比公司
        前置: 已确认
        步骤: GET /comparables
        期望: 200，返回已确认列表含 PE/PB 指标
        """
        resp = client.get(f"{API}/companies/comp_001/comparables")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["company_id"] == "comp_001"
        comps = data["comparables"]
        assert isinstance(comps, list)
        assert len(comps) > 0
        for c in comps:
            assert "comparable_id" in c
            assert "name" in c
            assert "pe" in c
            assert "pb" in c
            assert "stock_price" in c
            assert "net_profit" in c
            assert "net_assets" in c
            assert "revenue" in c

    # ── TC-003-04 ────────────────────────────────────────────
    def test_TC003_04_empty_list_confirm(self, client):
        """TC-003-04 空列表确认
        前置: —
        步骤: PUT /comparables, ids=[]
        期望: 400, INVALID_PARAMS
        """
        resp = client.put(
            f"{API}/companies/comp_001/comparables",
            json={"comparable_ids": []},
            content_type="application/json",
        )
        assert resp.status_code == 400
        body = resp.get_json()
        assert body["error"]["code"] == "INVALID_PARAMS"

    # ── TC-003-05 ────────────────────────────────────────────
    def test_TC003_05_ai_unavailable_fallback(self, client):
        """TC-003-05 AI 不可用降级
        前置: AI 服务关闭
        步骤: POST /comparables/recommend
        期望: 500, AI_UNAVAILABLE
        Mock recommend_comparables 返回 None 模拟 AI 不可用
        """
        with patch("routes.comparables.recommend_comparables", return_value=None):
            resp = client.post(f"{API}/companies/comp_001/comparables/recommend")
        assert resp.status_code == 500
        body = resp.get_json()
        assert body["error"]["code"] == "AI_UNAVAILABLE"
