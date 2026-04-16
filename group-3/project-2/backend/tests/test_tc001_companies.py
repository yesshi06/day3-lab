"""TC-001: 公司管理 API 测试（US-001）— 5 个 P0 用例
对齐 Spec 13-测试策略与质量门禁 §1.1
"""
import time

API = "/api/v1/valuation"


class TestTC001Companies:
    """US-001 公司管理"""

    # ── TC-001-01 ────────────────────────────────────────────
    def test_TC001_01_get_company_list(self, client):
        """TC-001-01 公司列表正常返回
        前置: 有种子数据
        步骤: GET /companies
        期望: 200，返回 companies 数组
        """
        start = time.time()
        resp = client.get(f"{API}/companies")
        elapsed = time.time() - start

        assert resp.status_code == 200
        body = resp.get_json()
        assert "data" in body
        data = body["data"]
        assert "companies" in data
        assert isinstance(data["companies"], list)
        assert len(data["companies"]) > 0
        assert "total" in data
        # SLO: 公司列表响应 ≤ 1s
        assert elapsed <= 1.0, f"响应时间 {elapsed:.3f}s 超过 1s SLO"
        # 每个公司必须包含规定字段
        for c in data["companies"]:
            assert "company_id" in c
            assert "name" in c
            assert "industry" in c
            assert "has_valuation" in c

    # ── TC-001-02 ────────────────────────────────────────────
    def test_TC001_02_search_by_keyword(self, client):
        """TC-001-02 关键字搜索
        前置: 有种子数据
        步骤: GET /companies?keyword=字节
        期望: 200，仅返回匹配公司
        """
        resp = client.get(f"{API}/companies?keyword=字节")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["total"] >= 1
        for c in data["companies"]:
            assert "字节" in c["name"]

    # ── TC-001-03 ────────────────────────────────────────────
    def test_TC001_03_filter_by_industry(self, client):
        """TC-001-03 行业筛选
        前置: 有种子数据
        步骤: GET /companies?industry=互联网
        期望: 200，仅返回该行业公司
        """
        resp = client.get(f"{API}/companies?industry=互联网")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["total"] >= 1
        for c in data["companies"]:
            assert c["industry"] == "互联网"

    # ── TC-001-04 ────────────────────────────────────────────
    def test_TC001_04_get_company_detail(self, client):
        """TC-001-04 公司详情
        前置: 公司存在
        步骤: GET /companies/comp_001
        期望: 200，含 name/industry/industry_info
        """
        resp = client.get(f"{API}/companies/comp_001")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["company_id"] == "comp_001"
        assert "name" in data
        assert "industry" in data
        assert "industry_info" in data
        assert isinstance(data["industry_info"], dict)
        assert "avg_pe" in data["industry_info"]
        assert "has_financials" in data

    # ── TC-001-05 ────────────────────────────────────────────
    def test_TC001_05_company_not_found(self, client):
        """TC-001-05 公司不存在
        前置: —
        步骤: GET /companies/invalid_id
        期望: 404, COMPANY_NOT_FOUND
        """
        resp = client.get(f"{API}/companies/invalid_id")
        assert resp.status_code == 404
        body = resp.get_json()
        assert "error" in body
        assert body["error"]["code"] == "COMPANY_NOT_FOUND"
