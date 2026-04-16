"""TC-006: 全局测试 — 存储层单元测试 — 4 个 P0 用例
对齐 Spec 13-测试策略与质量门禁 §1.6
"""
import json
import os

API = "/api/v1/valuation"


class TestTC006Global:
    """全局存储层单元测试"""

    # ── TC-006-01 ────────────────────────────────────────────
    def test_TC006_01_company_crud(self, client, data_dir):
        """TC-006-01 公司 CRUD（JSON 存储 CRUD 验证）
        步骤: 增/查/改/删
        期望: 数据一致
        """
        # 查：列表
        resp = client.get(f"{API}/companies")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        initial_count = data["total"]
        assert initial_count > 0

        # 查：详情
        resp = client.get(f"{API}/companies/comp_001")
        assert resp.status_code == 200
        detail = resp.get_json()["data"]
        assert detail["name"] == "字节跳动"

        # 增（通过直接写 JSON 模拟）
        companies_path = os.path.join(data_dir, "companies.json")
        with open(companies_path, "r", encoding="utf-8") as f:
            companies = json.load(f)
        new_company = {
            "company_id": "comp_test",
            "name": "测试公司",
            "industry": "测试行业",
            "founded_year": 2024,
            "description": "测试",
        }
        companies.append(new_company)
        with open(companies_path, "w", encoding="utf-8") as f:
            json.dump(companies, f, ensure_ascii=False, indent=2)

        # 验证增加
        resp = client.get(f"{API}/companies")
        assert resp.get_json()["data"]["total"] == initial_count + 1

        # 改（修改名称）
        companies[-1]["name"] = "测试公司-修改"
        with open(companies_path, "w", encoding="utf-8") as f:
            json.dump(companies, f, ensure_ascii=False, indent=2)
        resp = client.get(f"{API}/companies/comp_test")
        assert resp.get_json()["data"]["name"] == "测试公司-修改"

        # 删
        companies = [c for c in companies if c["company_id"] != "comp_test"]
        with open(companies_path, "w", encoding="utf-8") as f:
            json.dump(companies, f, ensure_ascii=False, indent=2)
        resp = client.get(f"{API}/companies")
        assert resp.get_json()["data"]["total"] == initial_count

    # ── TC-006-02 ────────────────────────────────────────────
    def test_TC006_02_financial_period_overwrite(self, client, data_dir):
        """TC-006-02 财务数据同期覆盖
        步骤: 两次导入同一 period
        期望: 只保留最新数据
        """
        payload_v1 = {
            "period": "2026-TEST",
            "revenue": 1000000,
            "net_profit": 200000,
            "total_assets": 5000000,
            "net_assets": 3000000,
            "operating_cashflow": 250000,
        }
        resp1 = client.post(
            f"{API}/companies/comp_001/financials",
            json=payload_v1,
            content_type="application/json",
        )
        assert resp1.status_code == 201

        payload_v2 = {**payload_v1, "revenue": 2000000, "net_profit": 400000}
        resp2 = client.post(
            f"{API}/companies/comp_001/financials",
            json=payload_v2,
            content_type="application/json",
        )
        assert resp2.status_code == 201

        # 验证
        resp = client.get(f"{API}/companies/comp_001/financials")
        fins = resp.get_json()["data"]["financials"]
        test_records = [f for f in fins if f["period"] == "2026-TEST"]
        assert len(test_records) == 1, "同期数据应只保留一条"
        assert test_records[0]["revenue"] == 2000000
        assert test_records[0]["net_profit"] == 400000

    # ── TC-006-03 ────────────────────────────────────────────
    def test_TC006_03_comparable_confirm_lock(self, client, data_dir):
        """TC-006-03 可比公司确认锁定
        步骤: confirm 后查询
        期望: confirmed=true（即能查到已确认的列表）
        """
        ids = ["listed_001", "listed_002"]
        resp = client.put(
            f"{API}/companies/comp_001/comparables",
            json={"comparable_ids": ids},
            content_type="application/json",
        )
        assert resp.status_code == 200

        # 查询确认结果
        resp = client.get(f"{API}/companies/comp_001/comparables")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        comp_ids = [c["comparable_id"] for c in data["comparables"]]
        assert set(comp_ids) == set(ids), "确认后查询应返回已确认的可比公司"

        # 验证 JSON 文件中的持久化
        with open(os.path.join(data_dir, "comparables.json"), "r") as f:
            stored = json.load(f)
        assert "comp_001" in stored
        assert stored["comp_001"] == ids

    # ── TC-006-04 ────────────────────────────────────────────
    def test_TC006_04_valuation_overwrite(self, client, seeded_comparables, data_dir):
        """TC-006-04 估值覆盖
        步骤: 两次运行同方法
        期望: 旧记录被覆盖
        """
        # 第一次运行
        resp1 = client.post(
            f"{API}/companies/comp_001/valuations/run",
            json={},
            content_type="application/json",
        )
        assert resp1.status_code == 200
        methods1 = client.get(
            f"{API}/companies/comp_001/valuations/methods"
        ).get_json()["data"]["methods"]
        dcf1_mid = next(m for m in methods1 if m["method_name"] == "dcf")["valuation_mid"]

        # 第二次运行（不同参数）
        resp2 = client.post(
            f"{API}/companies/comp_001/valuations/run",
            json={"dcf_discount_rate": 0.15},
            content_type="application/json",
        )
        assert resp2.status_code == 200
        methods2 = client.get(
            f"{API}/companies/comp_001/valuations/methods"
        ).get_json()["data"]["methods"]
        dcf2_mid = next(m for m in methods2 if m["method_name"] == "dcf")["valuation_mid"]

        assert dcf1_mid != dcf2_mid, "重新估值应覆盖旧结果"

        # 验证 JSON 文件中只有最新结果
        with open(os.path.join(data_dir, "valuations.json"), "r") as f:
            stored = json.load(f)
        assert "comp_001" in stored
        dcf_params = stored["comp_001"]["dcf_params"]
        assert dcf_params["discount_rate"] == 0.15, "存储的应是最新的参数"
