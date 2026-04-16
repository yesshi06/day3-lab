# 09 — API 接口规格

---

| 项 | 值 |
|---|---|
| 模块编号 | M2-VAL |
| 模块名称 | 公司估值系统 |
| 文档版本 | v0.1 |
| 阶段 | Design（How — 契约真源） |
| Base URL | `/api/v1/valuation` |
| 技术栈 | 后端 Flask + JSON 文件存储 · 前端 React + Vite · pytest 测试 |

---

> **本文是全部 API 端点的契约真源**。`05` 定义"用户要什么"，**09（本文）定义"后端必须返回什么"**，`13` 的测试断言以本文为准。
>
> **需求来源**：
> - US-001（P0）目标公司选择与筛选 → REQ-M2VAL-001
> - US-002（P0）目标公司详情与财务数据 → REQ-M2VAL-002
> - US-003（P0）可比公司AI推荐与确认 → REQ-M2VAL-003
> - US-004（P0）多方法估值分析 → REQ-M2VAL-004
> - US-005（P0）估值结果综合展示 → REQ-M2VAL-005

## 1. 端点总览

| # | 端点 | 方法 | 功能 | 对应需求 | 成功码 |
|---|------|------|------|----------|--------|
| 1 | `/api/v1/valuation/companies` | GET | 公司列表（搜索/筛选） | REQ-M2VAL-001 | 200 |
| 2 | `/api/v1/valuation/companies/<id>` | GET | 公司详情 | REQ-M2VAL-002 | 200 |
| 3 | `/api/v1/valuation/companies/<id>/financials` | POST | 导入财务数据 | REQ-M2VAL-002 | 201 |
| 4 | `/api/v1/valuation/companies/<id>/financials` | GET | 获取财务数据 | REQ-M2VAL-002 | 200 |
| 5 | `/api/v1/valuation/companies/<id>/comparables/recommend` | POST | AI推荐可比公司 | REQ-M2VAL-003 | 200 |
| 6 | `/api/v1/valuation/companies/<id>/comparables` | PUT | 确认/更新可比公司 | REQ-M2VAL-003 | 200 |
| 7 | `/api/v1/valuation/companies/<id>/comparables` | GET | 获取已确认可比公司 | REQ-M2VAL-003 | 200 |
| 8 | `/api/v1/valuation/companies/<id>/valuations/run` | POST | 运行估值计算 | REQ-M2VAL-004 | 200 |
| 9 | `/api/v1/valuation/companies/<id>/valuations/methods` | GET | 获取各方法估值详情 | REQ-M2VAL-004 | 200 |
| 10 | `/api/v1/valuation/companies/<id>/valuations/summary` | GET | 估值结果综合摘要 | REQ-M2VAL-005 | 200 |

## 2. 统一响应规范

### 成功响应

```json
{ "traceId": "tr_abc123...", /* 业务字段 */ }
```

### 错误响应

```json
{ "error": { "code": "COMPANY_NOT_FOUND", "message": "公司不存在", "details": {}, "traceId": "tr_..." } }
```

### 错误码清单

| HTTP | error.code | 触发条件 | details |
|------|-----------|----------|---------|
| 400 | `MISSING_COMPANY_ID` | company_id 为空 | `{}` |
| 400 | `INVALID_FINANCIAL_DATA` | 财务数据格式不合法或缺少必填字段 | `{"missing_fields":["..."]}` |
| 400 | `NO_COMPARABLES` | 未确认可比公司即发起估值计算 | `{}` |
| 400 | `INVALID_PARAMS` | DCF 调参数值超出合理范围 | `{"field":"discount_rate","range":"0.01~0.30"}` |
| 404 | `COMPANY_NOT_FOUND` | company_id 对应的公司不存在 | `{"company_id":"..."}` |
| 404 | `VALUATION_NOT_FOUND` | 该公司尚未运行估值 | `{"company_id":"..."}` |
| 500 | `AI_UNAVAILABLE` | AI 推荐服务不可用 | `{}` |
| 500 | `INTERNAL_ERROR` | 服务器内部错误 | `{}` |

## 3. GET /companies — 公司列表

> 对应 US-001（P0），需求编号 REQ-M2VAL-001。
> 验收标准：AC-001-01 按名称搜索 1s 内返回；AC-001-02 按行业筛选。

**查询参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `keyword` | string | 否 | — | 公司名称关键字搜索 |
| `industry` | string | 否 | — | 行业分类筛选 |
| `page` | integer | 否 | 1 | 页码 |
| `page_size` | integer | 否 | 20 | 每页条数，最大 100 |

**成功响应**（200）：

| 字段 | 类型 | 必有 | 说明 |
|------|------|------|------|
| `traceId` | string | 是 | 链路追踪 ID |
| `total` | integer | 是 | 匹配总数 |
| `companies` | array | 是 | 公司列表 |
| `companies[].company_id` | string | 是 | 公司唯一 ID |
| `companies[].name` | string | 是 | 公司名称 |
| `companies[].industry` | string | 是 | 行业分类 |
| `companies[].has_valuation` | boolean | 是 | 是否已有估值记录 |

**响应示例**：

```json
{
  "traceId": "tr_comp_001",
  "total": 2,
  "companies": [
    { "company_id": "comp_001", "name": "字节跳动", "industry": "互联网", "has_valuation": false },
    { "company_id": "comp_002", "name": "米哈游", "industry": "游戏", "has_valuation": true }
  ]
}
```

## 4. GET /companies/\<id\> — 公司详情

> 对应 US-002（P0），需求编号 REQ-M2VAL-002。
> 验收标准：AC-002-01 展示基本信息；AC-002-04 行业情况。

**路径参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | **是** | 公司 ID |

**成功响应**（200）：

| 字段 | 类型 | 必有 | 说明 |
|------|------|------|------|
| `traceId` | string | 是 | 链路追踪 ID |
| `company_id` | string | 是 | 公司唯一 ID |
| `name` | string | 是 | 公司名称 |
| `industry` | string | 是 | 行业分类 |
| `founded_year` | integer | 否 | 成立年份 |
| `description` | string | 否 | 公司简介 |
| `industry_info` | object | 是 | 行业情况 |
| `industry_info.avg_pe` | number | 否 | 行业平均 PE |
| `industry_info.growth_rate` | number | 否 | 行业增速（%） |
| `has_financials` | boolean | 是 | 是否已有财务数据 |

**响应示例**：

```json
{
  "traceId": "tr_detail_001",
  "company_id": "comp_001",
  "name": "字节跳动",
  "industry": "互联网",
  "founded_year": 2012,
  "description": "全球领先的内容平台公司",
  "industry_info": { "avg_pe": 25.3, "growth_rate": 12.5 },
  "has_financials": true
}
```

## 5. POST /companies/\<id\>/financials — 导入财务数据

> 对应 US-002（P0），需求编号 REQ-M2VAL-002。
> 验收标准：AC-002-02 三表核心数据；AC-002-03 支持导入。

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `period` | string | **是** | 财务期间，如 "2025-Q4" 或 "2025-FY" |
| `revenue` | number | **是** | 营收（万元） |
| `net_profit` | number | **是** | 净利润（万元） |
| `total_assets` | number | **是** | 总资产（万元） |
| `net_assets` | number | **是** | 净资产（万元） |
| `operating_cashflow` | number | **是** | 经营现金流（万元） |
| `eps` | number | 否 | 每股净利润 |
| `stock_price` | number | 否 | 股价（上市公司必填） |

**成功响应**（201）：

```json
{
  "traceId": "tr_fin_001",
  "message": "财务数据导入成功",
  "company_id": "comp_001",
  "period": "2025-FY",
  "fields_imported": 7
}
```

## 6. GET /companies/\<id\>/financials — 获取财务数据

> 对应 US-002（P0），需求编号 REQ-M2VAL-002。

**成功响应**（200）：

| 字段 | 类型 | 必有 | 说明 |
|------|------|------|------|
| `traceId` | string | 是 | 链路追踪 ID |
| `company_id` | string | 是 | 公司 ID |
| `financials` | array | 是 | 各期财务数据列表 |
| `financials[].period` | string | 是 | 期间 |
| `financials[].revenue` | number | 是 | 营收（万元） |
| `financials[].net_profit` | number | 是 | 净利润（万元） |
| `financials[].total_assets` | number | 是 | 总资产（万元） |
| `financials[].net_assets` | number | 是 | 净资产（万元） |
| `financials[].operating_cashflow` | number | 是 | 经营现金流（万元） |
| `financials[].eps` | number | 否 | 每股净利润 |
| `financials[].stock_price` | number | 否 | 股价 |

**响应示例**：

```json
{
  "traceId": "tr_fin_002",
  "company_id": "comp_001",
  "financials": [
    {
      "period": "2025-FY",
      "revenue": 6000000,
      "net_profit": 1200000,
      "total_assets": 15000000,
      "net_assets": 8000000,
      "operating_cashflow": 1500000,
      "eps": null,
      "stock_price": null
    }
  ]
}
```

## 7. POST /companies/\<id\>/comparables/recommend — AI 推荐可比公司

> 对应 US-003（P0），需求编号 REQ-M2VAL-003。
> 验收标准：AC-003-01 返回 4~6 家 + 推荐理由；AC-003-04 AI 不可用降级提示。

**请求体**：无（基于目标公司已有信息自动推荐）。

**成功响应**（200）：

| 字段 | 类型 | 必有 | 说明 |
|------|------|------|------|
| `traceId` | string | 是 | 链路追踪 ID |
| `company_id` | string | 是 | 目标公司 ID |
| `recommendations` | array | 是 | 推荐可比公司列表（4~6 家） |
| `recommendations[].comparable_id` | string | 是 | 可比公司 ID |
| `recommendations[].name` | string | 是 | 公司名称 |
| `recommendations[].industry` | string | 是 | 行业 |
| `recommendations[].reason` | string | 是 | 推荐理由 |
| `recommendations[].similarity_score` | number | 是 | 相似度分数 0~1 |

**响应示例**：

```json
{
  "traceId": "tr_rec_001",
  "company_id": "comp_001",
  "recommendations": [
    { "comparable_id": "listed_001", "name": "腾讯控股", "industry": "互联网", "reason": "同为互联网平台型公司，营收规模相近", "similarity_score": 0.92 },
    { "comparable_id": "listed_002", "name": "快手科技", "industry": "互联网", "reason": "短视频赛道直接竞争对手", "similarity_score": 0.88 },
    { "comparable_id": "listed_003", "name": "哔哩哔哩", "industry": "互联网", "reason": "内容平台业务模式相似", "similarity_score": 0.81 },
    { "comparable_id": "listed_004", "name": "Meta Platforms", "industry": "互联网", "reason": "全球社交+广告业务对标", "similarity_score": 0.78 }
  ]
}
```

## 8. PUT /companies/\<id\>/comparables — 确认/更新可比公司

> 对应 US-003（P0），需求编号 REQ-M2VAL-003。
> 验收标准：AC-003-02 勾选/取消/手动添加；AC-003-03 确认后锁定。

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `comparable_ids` | array\<string\> | **是** | 已确认的可比公司 ID 列表，1~10 家 |

**成功响应**（200）：

```json
{
  "traceId": "tr_conf_001",
  "company_id": "comp_001",
  "confirmed_count": 4,
  "comparable_ids": ["listed_001", "listed_002", "listed_003", "listed_004"]
}
```

## 9. GET /companies/\<id\>/comparables — 获取已确认可比公司

> 对应 US-003（P0），需求编号 REQ-M2VAL-003。

**成功响应**（200）：

| 字段 | 类型 | 必有 | 说明 |
|------|------|------|------|
| `traceId` | string | 是 | 链路追踪 ID |
| `company_id` | string | 是 | 目标公司 ID |
| `comparables` | array | 是 | 已确认可比公司列表 |
| `comparables[].comparable_id` | string | 是 | 可比公司 ID |
| `comparables[].name` | string | 是 | 公司名称 |
| `comparables[].industry` | string | 是 | 行业 |
| `comparables[].stock_price` | number | 是 | 最新股价 |
| `comparables[].pe` | number | 是 | PE 值 |
| `comparables[].pb` | number | 是 | P/B 值 |
| `comparables[].net_profit` | number | 是 | 净利润（万元） |
| `comparables[].net_assets` | number | 是 | 净资产（万元） |
| `comparables[].revenue` | number | 是 | 营收（万元） |

**响应示例**：

```json
{
  "traceId": "tr_comp_list_001",
  "company_id": "comp_001",
  "comparables": [
    { "comparable_id": "listed_001", "name": "腾讯控股", "industry": "互联网", "stock_price": 380.0, "pe": 22.5, "pb": 4.8, "net_profit": 12500000, "net_assets": 5800000, "revenue": 55000000 },
    { "comparable_id": "listed_002", "name": "快手科技", "industry": "互联网", "stock_price": 55.0, "pe": 28.3, "pb": 3.2, "net_profit": 800000, "net_assets": 950000, "revenue": 11000000 }
  ]
}
```

## 10. POST /companies/\<id\>/valuations/run — 运行估值计算

> 对应 US-004（P0），需求编号 REQ-M2VAL-004。
> 前置条件：可比公司已确认（US-003 完成）。
> 验收标准：AC-004-02 PE 计算；AC-004-03 DCF 可调参；AC-004-04 P/B 计算；AC-004-05 至少 3 种并行。

**请求体**（可选，用于 DCF 调参）：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `dcf_discount_rate` | number | 否 | 0.10 | DCF 折现率（1%~30%） |
| `dcf_growth_rate` | number | 否 | 0.05 | DCF 永续增长率（0%~15%） |
| `dcf_projection_years` | integer | 否 | 5 | DCF 预测年数（3~10） |

**成功响应**（200）：

```json
{
  "traceId": "tr_val_run_001",
  "company_id": "comp_001",
  "methods_computed": 3,
  "methods": ["pe_comparable", "dcf", "pb"],
  "message": "估值计算完成，请查看详情"
}
```

## 11. GET /companies/\<id\>/valuations/methods — 各方法估值详情

> 对应 US-004（P0），需求编号 REQ-M2VAL-004。
> 验收标准：AC-004-01 展示可比公司指标；AC-004-02~05 各方法计算详情。

**成功响应**（200）：

| 字段 | 类型 | 必有 | 说明 |
|------|------|------|------|
| `traceId` | string | 是 | 链路追踪 ID |
| `company_id` | string | 是 | 目标公司 ID |
| `target_net_profit` | number | 是 | 目标公司净利润（万元） |
| `target_net_assets` | number | 是 | 目标公司净资产（万元） |
| `methods` | array | 是 | 各估值方法详情列表 |
| `methods[].method_name` | string | 是 | 方法名称：pe_comparable / dcf / pb |
| `methods[].valuation_low` | number | 是 | 估值下限（万元） |
| `methods[].valuation_mid` | number | 是 | 估值中位数（万元） |
| `methods[].valuation_high` | number | 是 | 估值上限（万元） |
| `methods[].params` | object | 是 | 该方法的核心参数 |
| `methods[].calculation_detail` | string | 是 | 计算过程文字说明 |

**响应示例**：

```json
{
  "traceId": "tr_methods_001",
  "company_id": "comp_001",
  "target_net_profit": 1200000,
  "target_net_assets": 8000000,
  "methods": [
    {
      "method_name": "pe_comparable",
      "valuation_low": 24000000,
      "valuation_mid": 27000000,
      "valuation_high": 34000000,
      "params": {
        "comparable_pe_median": 22.5,
        "comparable_pe_range": [18.0, 28.3],
        "comparable_companies": ["腾讯控股", "快手科技", "哔哩哔哩", "Meta"]
      },
      "calculation_detail": "取4家可比公司PE中位数22.5，乘以目标公司净利润1200000万元，得估值27000000万元"
    },
    {
      "method_name": "dcf",
      "valuation_low": 20000000,
      "valuation_mid": 25000000,
      "valuation_high": 30000000,
      "params": {
        "discount_rate": 0.10,
        "growth_rate": 0.05,
        "projection_years": 5,
        "base_cashflow": 1500000
      },
      "calculation_detail": "基于经营现金流1500000万元，5年预测期，折现率10%，永续增长率5%"
    },
    {
      "method_name": "pb",
      "valuation_low": 25600000,
      "valuation_mid": 32000000,
      "valuation_high": 38400000,
      "params": {
        "comparable_pb_median": 4.0,
        "comparable_pb_range": [3.2, 4.8]
      },
      "calculation_detail": "取可比公司PB中位数4.0，乘以目标公司净资产8000000万元，得估值32000000万元"
    }
  ]
}
```

## 12. GET /companies/\<id\>/valuations/summary — 估值结果综合摘要

> 对应 US-005（P0），需求编号 REQ-M2VAL-005。
> 验收标准：AC-005-01 各方法区间；AC-005-02 估值中枢；AC-005-03 AI 总结推荐。

**成功响应**（200）：

| 字段 | 类型 | 必有 | 说明 |
|------|------|------|------|
| `traceId` | string | 是 | 链路追踪 ID |
| `company_id` | string | 是 | 目标公司 ID |
| `company_name` | string | 是 | 目标公司名称 |
| `valuation_center` | number | 是 | 估值中枢（各方法中位数的简单平均，万元） |
| `methods_summary` | array | 是 | 各方法摘要 |
| `methods_summary[].method_name` | string | 是 | 方法名称 |
| `methods_summary[].valuation_range` | string | 是 | 估值区间展示文本 |
| `methods_summary[].valuation_mid` | number | 是 | 估值中位数（万元） |
| `ai_recommendation` | object | 是 | AI 总结推荐 |
| `ai_recommendation.recommended_method` | string | 是 | 推荐方法名称 |
| `ai_recommendation.reason` | string | 是 | 推荐理由 |
| `ai_recommendation.summary` | string | 是 | 综合总结文本 |

**响应示例**：

```json
{
  "traceId": "tr_summary_001",
  "company_id": "comp_001",
  "company_name": "字节跳动",
  "valuation_center": 28000000,
  "methods_summary": [
    { "method_name": "PE可比法", "valuation_range": "2.4万亿 ~ 3.4万亿", "valuation_mid": 27000000 },
    { "method_name": "DCF法", "valuation_range": "2.0万亿 ~ 3.0万亿", "valuation_mid": 25000000 },
    { "method_name": "P/B法", "valuation_range": "2.56万亿 ~ 3.84万亿", "valuation_mid": 32000000 }
  ],
  "ai_recommendation": {
    "recommended_method": "PE可比法",
    "reason": "目标公司处于成熟期互联网行业，盈利稳定，PE可比法最能反映市场对该行业的估值共识",
    "summary": "综合三种估值方法，字节跳动估值中枢约2.8万亿元。考虑到公司盈利能力稳定且可比公司样本充足，PE可比法（中位数2.7万亿）最具参考价值。DCF法受折现率假设影响较大，P/B法因轻资产属性偏高，建议以PE法为锚。"
  }
}
```

## 13. 参数校验规则汇总

| 端点 | 字段 | 规则 | 失败 HTTP | error.code |
|------|------|------|-----------|-----------|
| GET /companies | `page_size` | 1~100 | 400 | `INVALID_PARAMS` |
| POST /financials | `revenue` 等 | 数值型，非负 | 400 | `INVALID_FINANCIAL_DATA` |
| POST /financials | 必填字段 | revenue/net_profit/total_assets/net_assets/operating_cashflow | 400 | `INVALID_FINANCIAL_DATA` |
| PUT /comparables | `comparable_ids` | 数组长度 1~10 | 400 | `INVALID_PARAMS` |
| POST /valuations/run | 前置 | 必须已确认可比公司 | 400 | `NO_COMPARABLES` |
| POST /valuations/run | `dcf_discount_rate` | 0.01~0.30 | 400 | `INVALID_PARAMS` |
| POST /valuations/run | `dcf_growth_rate` | 0~0.15 | 400 | `INVALID_PARAMS` |
| 所有含 \<id\> | `id` | 公司必须存在 | 404 | `COMPANY_NOT_FOUND` |
| GET /methods, /summary | — | 必须先运行估值 | 404 | `VALUATION_NOT_FOUND` |

---

## 需求追溯总索引

| 需求编号 | UserStory | 优先级 | →06 功能 | →09 接口（本文） | →13 测试 | →14 追溯 |
|----------|-----------|--------|----------|------------------|----------|----------|
| REQ-M2VAL-001 | 目标公司选择与筛选 | P0 | §公司筛选页 | GET /companies | TC-001 | 行1 |
| REQ-M2VAL-002 | 目标公司详情与财务数据 | P0 | §公司详情页 | GET/POST /companies/{id} + /financials | TC-002 | 行2 |
| REQ-M2VAL-003 | 可比公司AI推荐与确认 | P0 | §可比公司推荐页 | POST /recommend + PUT/GET /comparables | TC-003 | 行3 |
| REQ-M2VAL-004 | 多方法估值分析 | P0 | §估值分析页 | POST /valuations/run + GET /methods | TC-004 | 行4 |
| REQ-M2VAL-005 | 估值结果综合展示 | P0 | §估值结果页 | GET /valuations/summary | TC-005 | 行5 |

---

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-04-14 | 首版填写，10 个端点完整定义 |
