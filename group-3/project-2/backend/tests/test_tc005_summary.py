"""TC-005: 估值结果 API 测试（US-005）— 3 个 P0 用例
对齐 Spec 13-测试策略与质量门禁 §1.5
"""

API = "/api/v1/valuation"


class TestTC005Summary:
    """US-005 估值结果"""

    # ── TC-005-01 ────────────────────────────────────────────
    def test_TC005_01_get_valuation_summary(self, client, seeded_valuation):
        """TC-005-01 获取估值摘要
        前置: 已运行估值
        步骤: GET /valuations/summary
        期望: 200，含 valuation_center + methods_summary
        """
        resp = client.get(f"{API}/companies/comp_001/valuations/summary")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["company_id"] == "comp_001"
        assert "company_name" in data
        assert "valuation_center" in data
        assert isinstance(data["valuation_center"], (int, float))
        assert data["valuation_center"] > 0
        assert "methods_summary" in data
        summaries = data["methods_summary"]
        assert isinstance(summaries, list)
        assert len(summaries) >= 3
        for s in summaries:
            assert "method_name" in s
            assert "valuation_range" in s
            assert "valuation_mid" in s

    # ── TC-005-02 ────────────────────────────────────────────
    def test_TC005_02_ai_recommendation_present(self, client, seeded_valuation):
        """TC-005-02 AI 总结存在
        前置: 已运行估值
        步骤: GET /valuations/summary
        期望: ai_recommendation 非空，含文字总结
        """
        resp = client.get(f"{API}/companies/comp_001/valuations/summary")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        ai = data["ai_recommendation"]
        assert ai is not None
        assert "recommended_method" in ai
        assert "reason" in ai
        assert "summary" in ai
        assert len(ai["summary"]) > 0, "AI 总结文本不应为空"

    # ── TC-005-03 ────────────────────────────────────────────
    def test_TC005_03_no_valuation_yet(self, client):
        """TC-005-03 未运行即查摘要
        前置: 无估值
        步骤: GET /valuations/summary
        期望: 404, VALUATION_NOT_FOUND
        """
        resp = client.get(f"{API}/companies/comp_001/valuations/summary")
        assert resp.status_code == 404
        body = resp.get_json()
        assert body["error"]["code"] == "VALUATION_NOT_FOUND"
