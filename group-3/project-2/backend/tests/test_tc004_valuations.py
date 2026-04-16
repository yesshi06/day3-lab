"""TC-004: 估值分析 API 测试（US-004）— 6 个 P0 用例
对齐 Spec 13-测试策略与质量门禁 §1.4
"""
import statistics
import time

API = "/api/v1/valuation"


class TestTC004Valuations:
    """US-004 估值分析"""

    # ── TC-004-01 ────────────────────────────────────────────
    def test_TC004_01_run_valuation_default(self, client, seeded_comparables):
        """TC-004-01 运行估值（默认参数）
        前置: 可比已确认
        步骤: POST /valuations/run
        期望: 200，methods_computed ≥ 3
        """
        start = time.time()
        resp = client.post(
            f"{API}/companies/comp_001/valuations/run",
            json={},
            content_type="application/json",
        )
        elapsed = time.time() - start

        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["company_id"] == "comp_001"
        assert data["methods_computed"] >= 3
        assert "methods" in data
        method_names = data["methods"]
        assert "pe_comparable" in method_names
        assert "dcf" in method_names
        assert "pb" in method_names
        assert data["message"] == "估值计算完成，请查看详情"
        # SLO: 估值计算 ≤ 5s
        assert elapsed <= 5.0, f"估值耗时 {elapsed:.3f}s 超过 5s SLO"

    # ── TC-004-02 ────────────────────────────────────────────
    def test_TC004_02_no_comparables(self, client):
        """TC-004-02 未确认可比即估值
        前置: 无可比
        步骤: POST /valuations/run
        期望: 400, NO_COMPARABLES
        """
        resp = client.post(
            f"{API}/companies/comp_001/valuations/run",
            json={},
            content_type="application/json",
        )
        assert resp.status_code == 400
        body = resp.get_json()
        assert body["error"]["code"] == "NO_COMPARABLES"

    # ── TC-004-03 ────────────────────────────────────────────
    def test_TC004_03_get_method_details(self, client, seeded_valuation):
        """TC-004-03 获取各方法详情
        前置: 已运行
        步骤: GET /valuations/methods
        期望: 200，含 pe/dcf/pb 三个方法
        """
        resp = client.get(f"{API}/companies/comp_001/valuations/methods")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["company_id"] == "comp_001"
        assert "target_net_profit" in data
        assert "target_net_assets" in data
        methods = data["methods"]
        assert isinstance(methods, list)
        assert len(methods) >= 3
        names = {m["method_name"] for m in methods}
        assert "pe_comparable" in names
        assert "dcf" in names
        assert "pb" in names
        for m in methods:
            assert "valuation_low" in m
            assert "valuation_mid" in m
            assert "valuation_high" in m
            assert "params" in m
            assert "calculation_detail" in m

    # ── TC-004-04 ────────────────────────────────────────────
    def test_TC004_04_pe_calculation_accuracy(self, client, seeded_valuation):
        """TC-004-04 PE 计算正确性
        前置: 已运行
        步骤: 校验 valuation_mid = PE中位数 × 净利润
        期望: 数值 100% 精度匹配
        """
        resp = client.get(f"{API}/companies/comp_001/valuations/methods")
        data = resp.get_json()["data"]
        target_net_profit = data["target_net_profit"]

        pe_method = next(m for m in data["methods"] if m["method_name"] == "pe_comparable")
        pe_median = pe_method["params"]["comparable_pe_median"]
        expected_mid = round(pe_median * target_net_profit)
        assert pe_method["valuation_mid"] == expected_mid, (
            f"PE估值中位数 {pe_method['valuation_mid']} != "
            f"PE中位数({pe_median}) × 净利润({target_net_profit}) = {expected_mid}"
        )

        # 额外验证 PE 中位数计算正确性
        pe_range = pe_method["params"]["comparable_pe_range"]
        assert pe_method["valuation_low"] == round(pe_range[0] * target_net_profit)
        assert pe_method["valuation_high"] == round(pe_range[1] * target_net_profit)

    # ── TC-004-05 ────────────────────────────────────────────
    def test_TC004_05_dcf_re_run_with_new_params(self, client, seeded_comparables):
        """TC-004-05 DCF 调参重算
        前置: 已运行
        步骤: POST /valuations/run, discount_rate=0.12
        期望: 200，DCF 结果变化
        """
        # 首次运行（默认参数）
        resp1 = client.post(
            f"{API}/companies/comp_001/valuations/run",
            json={},
            content_type="application/json",
        )
        assert resp1.status_code == 200
        methods1 = client.get(f"{API}/companies/comp_001/valuations/methods").get_json()["data"]["methods"]
        dcf1 = next(m for m in methods1 if m["method_name"] == "dcf")

        # 第二次运行（新折现率）
        resp2 = client.post(
            f"{API}/companies/comp_001/valuations/run",
            json={"dcf_discount_rate": 0.12},
            content_type="application/json",
        )
        assert resp2.status_code == 200
        methods2 = client.get(f"{API}/companies/comp_001/valuations/methods").get_json()["data"]["methods"]
        dcf2 = next(m for m in methods2 if m["method_name"] == "dcf")

        # DCF 结果应变化
        assert dcf1["valuation_mid"] != dcf2["valuation_mid"], (
            "调参后 DCF 估值中位数应变化"
        )
        assert dcf2["params"]["discount_rate"] == 0.12

    # ── TC-004-06 ────────────────────────────────────────────
    def test_TC004_06_invalid_dcf_params(self, client, seeded_comparables):
        """TC-004-06 DCF 参数越界
        前置: —
        步骤: POST /valuations/run, discount_rate=0.50
        期望: 400, INVALID_PARAMS
        """
        resp = client.post(
            f"{API}/companies/comp_001/valuations/run",
            json={"dcf_discount_rate": 0.50},
            content_type="application/json",
        )
        assert resp.status_code == 400
        body = resp.get_json()
        assert body["error"]["code"] == "INVALID_PARAMS"
        assert body["error"]["details"]["field"] == "dcf_discount_rate"
