# 09 — API 接口规格

---

| 项 | 值 |
|---|---|
| 模块编号 | M2-VAL |
| 模块名称 | 公司估值系统 |
| 文档版本 | v0.2.2 |
| 阶段 | Design（How — 契约真源） |
| Base URL | `/api/v1/valuation` |
| 技术栈 | 后端 Flask + JSON 文件存储 · 前端 React + Vite · pytest 测试 |
| 原型依据 | `prototype.html`（5 页交互原型，含统计卡片与多图表展示） |

---

> **本文是全部 API 端点的契约真源**。`05` 定义“用户要什么”，**09（本文）定义“后端必须返回什么”**，前端渲染和后端返回字段均以本文为准。
>
> **v0.2 更新目标**：基于当前原型图，把“前端要展示什么”翻译成“后端必须返回什么”，避免后端只返回基础表数据、却缺少图表和摘要所需字段。
>
> **Demo 约束**：这是一个 demo 级项目，前端选中公司后，由后端基于内置样例数据或预置数据源自动查找并返回公司详情、财务数据和估值结果；**不提供前端上传财务数据，也不提供结果导出接口**。

## 1. 设计原则

1. 页面上所有可见模块都必须能被 API 直接驱动，不依赖前端硬编码模拟数据。
2. 优先返回“可直接渲染”的结构化字段，减少前端二次拼装成本。
3. 列表页、详情页、估值页、结果页分开建模，避免一个接口承载过多职责。
4. 图表数据尽量跟业务数据同源，但允许在响应中增加聚合结果，降低前端重复计算。
5. Demo 版本默认由后端自动返回预置财务数据和估值数据，不设计文件导入与导出链路。

---

## 2. 端点总览

| # | 端点 | 方法 | 功能 | 对应页面 | 对应需求 | 成功码 |
|---|------|------|------|----------|----------|--------|
| 1 | `/companies` | GET | 公司列表（搜索/筛选） | 公司列表 | REQ-M2VAL-001 | 200 |
| 2 | `/statistics` | GET | 公司列表页统计与图表数据 | 公司列表 | REQ-M2VAL-001 | 200 |
| 3 | `/companies/<id>` | GET | 公司详情与行业信息 | 公司详情 | REQ-M2VAL-002 | 200 |
| 4 | `/companies/<id>/financials` | GET | 财务时序数据与财务比率 | 公司详情 | REQ-M2VAL-002 | 200 |
| 5 | `/companies/<id>/comparables/recommend` | POST | AI 推荐可比公司 | 可比公司 | REQ-M2VAL-003 | 200 |
| 6 | `/companies/<id>/comparables/candidates` | GET | 手动添加可比公司候选搜索 | 可比公司 | REQ-M2VAL-003 | 200 |
| 7 | `/companies/<id>/comparables` | PUT | 确认可比公司列表 | 可比公司 | REQ-M2VAL-003 | 200 |
| 8 | `/companies/<id>/comparables` | GET | 已确认可比公司及指标 | 可比公司 | REQ-M2VAL-003 | 200 |
| 9 | `/companies/<id>/valuations/run` | POST | 运行估值计算 | 估值分析 | REQ-M2VAL-004 | 200 |
| 10 | `/companies/<id>/valuations/methods` | GET | 各方法估值详情与图表数据 | 估值分析 | REQ-M2VAL-004 | 200 |
| 11 | `/companies/<id>/valuations/summary` | GET | 估值结果综合摘要 | 估值结果 | REQ-M2VAL-005 | 200 |

> 完整路径统一以 `/api/v1/valuation` 为前缀，例如：`/api/v1/valuation/companies`。

---

## 3. 统一响应规范

### 3.1 成功响应

```json
{
  "traceId": "tr_abc123...",
  "data": {}
}
```

### 3.2 错误响应

```json
{
  "error": {
    "code": "COMPANY_NOT_FOUND",
    "message": "公司不存在",
    "details": {},
    "traceId": "tr_..."
  }
}
```

### 3.3 错误码清单

| HTTP | error.code | 触发条件 | details |
|------|-----------|----------|---------|
| 400 | `MISSING_COMPANY_ID` | company_id 为空 | `{}` |
| 400 | `NO_COMPARABLES` | 未确认可比公司即发起估值计算 | `{}` |
| 400 | `INVALID_PARAMS` | 参数超出合理范围 | `{"field":"discount_rate","range":"0.01~0.30"}` |
| 404 | `COMPANY_NOT_FOUND` | company_id 对应公司不存在 | `{"company_id":"..."}` |
| 404 | `FINANCIALS_NOT_FOUND` | 后端未找到该公司的预置财务数据 | `{"company_id":"..."}` |
| 404 | `VALUATION_NOT_FOUND` | 尚未生成估值结果 | `{"company_id":"..."}` |
| 500 | `AI_UNAVAILABLE` | AI 推荐服务不可用 | `{}` |
| 500 | `INTERNAL_ERROR` | 服务内部错误 | `{}` |

---

## 4. GET /companies — 公司列表

> 对应 US-001（P0），需求编号 REQ-M2VAL-001。
> 用于驱动原型图中的“搜索结果表格”。

### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `keyword` | string | 否 | — | 公司名称关键字搜索 |
| `industry` | string | 否 | — | 行业分类筛选 |
| `page` | integer | 否 | 1 | 页码 |
| `page_size` | integer | 否 | 20 | 每页条数，最大 100 |

### 成功响应（200）

| 字段 | 类型 | 必有 | 说明 |
|------|------|------|------|
| `traceId` | string | 是 | 链路追踪 ID |
| `data.total` | integer | 是 | 匹配总数 |
| `data.page` | integer | 是 | 当前页码 |
| `data.page_size` | integer | 是 | 每页条数 |
| `data.companies` | array | 是 | 公司列表 |
| `data.companies[].company_id` | string | 是 | 公司唯一 ID |
| `data.companies[].name` | string | 是 | 公司名称 |
| `data.companies[].industry` | string | 是 | 行业分类 |
| `data.companies[].has_valuation` | boolean | 是 | 是否已有估值记录 |

### 响应示例

```json
{
  "traceId": "tr_comp_001",
  "data": {
    "total": 6,
    "page": 1,
    "page_size": 20,
    "companies": [
      { "company_id": "comp_001", "name": "字节跳动", "industry": "互联网", "has_valuation": false },
      { "company_id": "comp_002", "name": "米哈游", "industry": "游戏", "has_valuation": true },
      { "company_id": "comp_003", "name": "蚂蚁集团", "industry": "金融科技", "has_valuation": false },
      { "company_id": "comp_004", "name": "大疆创新", "industry": "智能硬件", "has_valuation": true },
      { "company_id": "comp_005", "name": "SpaceX", "industry": "航天", "has_valuation": false },
      { "company_id": "comp_006", "name": "Shein", "industry": "电商", "has_valuation": false }
    ]
  }
}
```

---

## 5. GET /statistics — 公司列表页统计与图表数据

> 对应 US-001（P0），需求编号 REQ-M2VAL-001。
> 该接口用于驱动原型图中的：
> - 4 个顶部统计卡片
> - 行业分布饼图
> - 估值状态分布饼图
> - 各行业平均 PE 柱状图

### 查询参数

无。

### 成功响应（200）

| 字段 | 类型 | 必有 | 说明 |
|------|------|------|------|
| `traceId` | string | 是 | 链路追踪 ID |
| `data.total_companies` | integer | 是 | 公司总数 |
| `data.valued_companies` | integer | 是 | 已估值公司数 |
| `data.valued_ratio` | number | 是 | 已估值占比，单位 % |
| `data.total_industries` | integer | 是 | 覆盖行业数 |
| `data.industry_groups` | integer | 是 | 行业大类数量，用于卡片副文案“6 大类” |
| `data.weekly_new_companies` | integer | 是 | 本周新增公司数 |
| `data.weekly_new_delta` | integer | 是 | 相比上周新增变化量，用于副文案“↑ 3 家” |
| `data.industry_distribution` | array | 是 | 行业分布 |
| `data.industry_distribution[].industry` | string | 是 | 行业名称 |
| `data.industry_distribution[].count` | integer | 是 | 公司数量 |
| `data.valuation_status` | object | 是 | 估值状态分布 |
| `data.valuation_status.valued` | integer | 是 | 已估值数量 |
| `data.valuation_status.not_valued` | integer | 是 | 未估值数量 |
| `data.industry_avg_pe` | array | 是 | 各行业平均 PE |
| `data.industry_avg_pe[].industry` | string | 是 | 行业名称 |
| `data.industry_avg_pe[].avg_pe` | number | 是 | 平均 PE |

### 响应示例

```json
{
  "traceId": "tr_stats_001",
  "data": {
    "total_companies": 128,
    "valued_companies": 47,
    "valued_ratio": 36.7,
    "total_industries": 12,
    "industry_groups": 6,
    "weekly_new_companies": 5,
    "weekly_new_delta": 3,
    "industry_distribution": [
      { "industry": "互联网", "count": 34 },
      { "industry": "游戏", "count": 18 },
      { "industry": "新能源", "count": 22 },
      { "industry": "半导体", "count": 15 },
      { "industry": "医药", "count": 12 },
      { "industry": "金融科技", "count": 10 },
      { "industry": "智能硬件", "count": 8 },
      { "industry": "其他", "count": 9 }
    ],
    "valuation_status": {
      "valued": 47,
      "not_valued": 81
    },
    "industry_avg_pe": [
      { "industry": "互联网", "avg_pe": 25.3 },
      { "industry": "游戏", "avg_pe": 32.1 },
      { "industry": "新能源", "avg_pe": 45.6 },
      { "industry": "半导体", "avg_pe": 38.2 },
      { "industry": "医药", "avg_pe": 28.9 },
      { "industry": "金融科技", "avg_pe": 15.4 }
    ]
  }
}
```

---

## 6. GET /companies/\<id\> — 公司详情与行业信息

> 对应 US-002（P0），需求编号 REQ-M2VAL-002。
> 用于驱动原型图中的“基本信息”“行业概况”“行业 PE 分布”。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | 是 | 公司 ID |

### 成功响应（200）

| 字段 | 类型 | 必有 | 说明 |
|------|------|------|------|
| `traceId` | string | 是 | 链路追踪 ID |
| `data.company_id` | string | 是 | 公司唯一 ID |
| `data.name` | string | 是 | 公司名称 |
| `data.industry` | string | 是 | 行业分类 |
| `data.founded_year` | integer | 否 | 成立年份 |
| `data.description` | string | 否 | 公司简介 |
| `data.has_financials` | boolean | 是 | 是否已有财务数据 |
| `data.industry_info` | object | 是 | 行业信息 |
| `data.industry_info.avg_pe` | number | 是 | 行业平均 PE |
| `data.industry_info.growth_rate` | number | 是 | 行业增速，单位 % |
| `data.industry_info.company_count` | integer | 是 | 行业公司数量 |
| `data.industry_info.pe_distribution` | array | 是 | 行业 PE 分布图数据 |
| `data.industry_info.pe_distribution[].range` | string | 是 | PE 区间标签 |
| `data.industry_info.pe_distribution[].count` | integer | 是 | 该区间公司数 |

### 响应示例

```json
{
  "traceId": "tr_detail_001",
  "data": {
    "company_id": "comp_001",
    "name": "字节跳动",
    "industry": "互联网",
    "founded_year": 2012,
    "description": "全球领先的内容平台公司",
    "has_financials": true,
    "industry_info": {
      "avg_pe": 25.3,
      "growth_rate": 12.5,
      "company_count": 34,
      "pe_distribution": [
        { "range": "<15", "count": 3 },
        { "range": "15-20", "count": 5 },
        { "range": "20-25", "count": 10 },
        { "range": "25-30", "count": 8 },
        { "range": "30-35", "count": 5 },
        { "range": ">35", "count": 3 }
      ]
    }
  }
}
```

---

## 7. GET /companies/\<id\>/financials — 财务时序数据与财务比率

> 对应 US-002（P0），需求编号 REQ-M2VAL-002。
> 用于驱动原型图中的：
> - 4 个财务统计卡片
> - 财务三表核心数据表格
> - 营收与净利润趋势图
> - 资产结构变化图
> - 经营现金流趋势图
> - 关键财务比率雷达图
> 
> 数据来源说明：前端只传公司 ID，后端根据预置样例数据自动查找并返回对应财务数据。

### 成功响应（200）

| 字段 | 类型 | 必有 | 说明 |
|------|------|------|------|
| `traceId` | string | 是 | 链路追踪 ID |
| `data.company_id` | string | 是 | 公司 ID |
| `data.latest_summary` | object | 是 | 最新一期摘要数据 |
| `data.latest_summary.period` | string | 是 | 最新期间 |
| `data.latest_summary.revenue` | number | 是 | 营收（万元） |
| `data.latest_summary.net_profit` | number | 是 | 净利润（万元） |
| `data.latest_summary.total_assets` | number | 是 | 总资产（万元） |
| `data.latest_summary.net_assets` | number | 是 | 净资产（万元） |
| `data.latest_summary.operating_cashflow` | number | 是 | 经营现金流（万元） |
| `data.latest_summary.yoy_revenue` | number | 是 | 营收同比，单位 % |
| `data.latest_summary.yoy_net_profit` | number | 是 | 净利润同比，单位 % |
| `data.latest_summary.yoy_net_assets` | number | 是 | 净资产同比，单位 % |
| `data.latest_summary.summary_note` | string | 否 | 摘要说明，如“稳健增长” |
| `data.financials` | array | 是 | 财务时序数据 |
| `data.financials[].period` | string | 是 | 期间 |
| `data.financials[].revenue` | number | 是 | 营收（万元） |
| `data.financials[].net_profit` | number | 是 | 净利润（万元） |
| `data.financials[].total_assets` | number | 是 | 总资产（万元） |
| `data.financials[].net_assets` | number | 是 | 净资产（万元） |
| `data.financials[].operating_cashflow` | number | 是 | 经营现金流（万元） |
| `data.financials[].eps` | number | 否 | 每股净利润 |
| `data.financials[].stock_price` | number | 否 | 股价 |
| `data.ratios` | object | 是 | 当前公司关键财务比率 |
| `data.ratios.net_profit_margin` | number | 是 | 净利润率，单位 % |
| `data.ratios.roa` | number | 是 | 资产回报率，单位 % |
| `data.ratios.revenue_growth` | number | 是 | 营收增速，单位 % |
| `data.ratios.cashflow_ratio` | number | 是 | 现金流比率，单位 % |
| `data.ratios.debt_ratio` | number | 是 | 资产负债率，单位 % |
| `data.industry_avg_ratios` | object | 是 | 行业平均比率，用于雷达图对比 |

### 响应示例

```json
{
  "traceId": "tr_fin_002",
  "data": {
    "company_id": "comp_001",
    "latest_summary": {
      "period": "2025-FY",
      "revenue": 6000000,
      "net_profit": 1200000,
      "total_assets": 15000000,
      "net_assets": 8000000,
      "operating_cashflow": 1500000,
      "yoy_revenue": 18.0,
      "yoy_net_profit": 22.0,
      "yoy_net_assets": 15.0,
      "summary_note": "稳健增长"
    },
    "financials": [
      { "period": "2025-FY", "revenue": 6000000, "net_profit": 1200000, "total_assets": 15000000, "net_assets": 8000000, "operating_cashflow": 1500000, "eps": null, "stock_price": null },
      { "period": "2024-FY", "revenue": 5100000, "net_profit": 980000, "total_assets": 12800000, "net_assets": 6950000, "operating_cashflow": 1250000, "eps": null, "stock_price": null },
      { "period": "2023-FY", "revenue": 4200000, "net_profit": 750000, "total_assets": 10500000, "net_assets": 5800000, "operating_cashflow": 980000, "eps": null, "stock_price": null },
      { "period": "2022-FY", "revenue": 3500000, "net_profit": 520000, "total_assets": 8900000, "net_assets": 4700000, "operating_cashflow": 720000, "eps": null, "stock_price": null },
      { "period": "2021-FY", "revenue": 2800000, "net_profit": 350000, "total_assets": 7200000, "net_assets": 3600000, "operating_cashflow": 550000, "eps": null, "stock_price": null }
    ],
    "ratios": {
      "net_profit_margin": 20.0,
      "roa": 8.0,
      "revenue_growth": 18.0,
      "cashflow_ratio": 25.0,
      "debt_ratio": 47.0
    },
    "industry_avg_ratios": {
      "net_profit_margin": 15.0,
      "roa": 6.0,
      "revenue_growth": 12.0,
      "cashflow_ratio": 20.0,
      "debt_ratio": 52.0
    }
  }
}
```

---

## 8. POST /companies/\<id\>/comparables/recommend — AI 推荐可比公司

> 对应 US-003（P0），需求编号 REQ-M2VAL-003。
> 用于驱动原型图中的 AI 推荐卡片和相似度雷达图。

### 请求体

无。

### 成功响应（200）

| 字段 | 类型 | 必有 | 说明 |
|------|------|------|------|
| `traceId` | string | 是 | 链路追踪 ID |
| `data.company_id` | string | 是 | 目标公司 ID |
| `data.prompt_summary` | string | 是 | 推荐说明文案 |
| `data.recommendations` | array | 是 | 推荐结果，建议 4~6 家 |
| `data.recommendations[].comparable_id` | string | 是 | 可比公司 ID |
| `data.recommendations[].name` | string | 是 | 公司名称 |
| `data.recommendations[].industry` | string | 是 | 行业 |
| `data.recommendations[].reason` | string | 是 | 推荐理由 |
| `data.recommendations[].similarity_score` | number | 是 | 综合相似度，0~1 |
| `data.recommendations[].similarity_dimensions` | object | 是 | 多维度相似度，用于雷达图 |
| `data.recommendations[].similarity_dimensions.industry` | number | 是 | 行业相似度，0~100 |
| `data.recommendations[].similarity_dimensions.scale` | number | 是 | 规模匹配度，0~100 |
| `data.recommendations[].similarity_dimensions.business_model` | number | 是 | 业务模式相似度，0~100 |
| `data.recommendations[].similarity_dimensions.profitability` | number | 是 | 盈利能力相似度，0~100 |
| `data.recommendations[].similarity_dimensions.growth` | number | 是 | 增长趋势相似度，0~100 |

### 响应示例

```json
{
  "traceId": "tr_rec_001",
  "data": {
    "company_id": "comp_001",
    "prompt_summary": "基于字节跳动的行业属性（互联网）、营收规模和业务模式，推荐以下 4 家可比上市公司。",
    "recommendations": [
      {
        "comparable_id": "listed_001",
        "name": "腾讯控股",
        "industry": "互联网",
        "reason": "同为互联网平台型公司，营收规模相近",
        "similarity_score": 0.92,
        "similarity_dimensions": {
          "industry": 95,
          "scale": 85,
          "business_model": 80,
          "profitability": 90,
          "growth": 75
        }
      },
      {
        "comparable_id": "listed_002",
        "name": "快手科技",
        "industry": "互联网",
        "reason": "短视频赛道直接竞争对手",
        "similarity_score": 0.88,
        "similarity_dimensions": {
          "industry": 98,
          "scale": 60,
          "business_model": 95,
          "profitability": 55,
          "growth": 85
        }
      },
      {
        "comparable_id": "listed_003",
        "name": "哔哩哔哩",
        "industry": "互联网",
        "reason": "内容平台业务模式相似",
        "similarity_score": 0.81,
        "similarity_dimensions": {
          "industry": 90,
          "scale": 40,
          "business_model": 85,
          "profitability": 35,
          "growth": 80
        }
      },
      {
        "comparable_id": "listed_004",
        "name": "Meta Platforms",
        "industry": "互联网",
        "reason": "全球社交+广告业务对标",
        "similarity_score": 0.78,
        "similarity_dimensions": {
          "industry": 70,
          "scale": 95,
          "business_model": 75,
          "profitability": 95,
          "growth": 70
        }
      }
    ]
  }
}
```

---

## 9. GET /companies/\<id\>/comparables/candidates — 手动添加可比公司候选搜索

> 对应 US-003（P0），需求编号 REQ-M2VAL-003。
> 对应原型图中的“＋ 手动添加公司”按钮。
> 该接口用于搜索可手动加入的上市可比公司候选，避免前端只能依赖 AI 推荐结果。

### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `keyword` | string | 否 | — | 公司名称关键字 |
| `industry` | string | 否 | — | 行业筛选 |
| `limit` | integer | 否 | 20 | 返回候选数量上限 |

### 成功响应（200）

| 字段 | 类型 | 必有 | 说明 |
|------|------|------|------|
| `traceId` | string | 是 | 链路追踪 ID |
| `data.company_id` | string | 是 | 当前目标公司 ID |
| `data.candidates` | array | 是 | 候选可比公司列表 |
| `data.candidates[].comparable_id` | string | 是 | 可比公司 ID |
| `data.candidates[].name` | string | 是 | 公司名称 |
| `data.candidates[].industry` | string | 是 | 行业 |
| `data.candidates[].stock_price` | number | 否 | 最新股价 |
| `data.candidates[].pe` | number | 否 | PE |
| `data.candidates[].pb` | number | 否 | P/B |
| `data.candidates[].market_hint` | string | 否 | 简短说明，如“港股 / 美股 / A股” |

### 响应示例

```json
{
  "traceId": "tr_comp_candidates_001",
  "data": {
    "company_id": "comp_001",
    "candidates": [
      { "comparable_id": "listed_005", "name": "微博", "industry": "互联网", "stock_price": 72.0, "pe": 19.6, "pb": 2.8, "market_hint": "美股" },
      { "comparable_id": "listed_006", "name": "知乎", "industry": "互联网", "stock_price": 14.2, "pe": null, "pb": 1.6, "market_hint": "美股" }
    ]
  }
}
```

---

## 10. PUT /companies/\<id\>/comparables — 确认可比公司列表

> 对应 US-003（P0），需求编号 REQ-M2VAL-003。

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `comparable_ids` | array<string> | 是 | 已确认可比公司 ID 列表，长度 1~10 |

### 成功响应（200）

```json
{
  "traceId": "tr_comp_confirm_001",
  "data": {
    "company_id": "comp_001",
    "confirmed_count": 4,
    "comparable_ids": ["listed_001", "listed_002", "listed_003", "listed_004"]
  }
}
```

---

## 11. GET /companies/\<id\>/comparables — 已确认可比公司及指标

> 对应 US-003（P0），需求编号 REQ-M2VAL-003。
> 用于驱动原型图中的可比公司明细表和 PE/PB 对比图。

### 成功响应（200）

| 字段 | 类型 | 必有 | 说明 |
|------|------|------|------|
| `traceId` | string | 是 | 链路追踪 ID |
| `data.company_id` | string | 是 | 目标公司 ID |
| `data.comparables` | array | 是 | 已确认可比公司列表 |
| `data.comparables[].comparable_id` | string | 是 | 可比公司 ID |
| `data.comparables[].name` | string | 是 | 公司名称 |
| `data.comparables[].industry` | string | 是 | 行业 |
| `data.comparables[].stock_price` | number | 是 | 最新股价 |
| `data.comparables[].pe` | number | 是 | PE |
| `data.comparables[].pb` | number | 是 | P/B |
| `data.comparables[].net_profit` | number | 是 | 净利润（万元） |
| `data.comparables[].net_assets` | number | 是 | 净资产（万元） |
| `data.comparables[].revenue` | number | 是 | 营收（万元） |

### 响应示例

```json
{
  "traceId": "tr_comp_list_001",
  "data": {
    "company_id": "comp_001",
    "comparables": [
      { "comparable_id": "listed_001", "name": "腾讯控股", "industry": "互联网", "stock_price": 380.0, "pe": 22.5, "pb": 4.8, "net_profit": 12500000, "net_assets": 5800000, "revenue": 55000000 },
      { "comparable_id": "listed_002", "name": "快手科技", "industry": "互联网", "stock_price": 55.0, "pe": 28.3, "pb": 3.2, "net_profit": 800000, "net_assets": 950000, "revenue": 11000000 },
      { "comparable_id": "listed_003", "name": "哔哩哔哩", "industry": "互联网", "stock_price": 18.5, "pe": 35.2, "pb": 2.1, "net_profit": 250000, "net_assets": 420000, "revenue": 6500000 },
      { "comparable_id": "listed_004", "name": "Meta Platforms", "industry": "互联网", "stock_price": 520.0, "pe": 18.8, "pb": 6.5, "net_profit": 39000000, "net_assets": 12000000, "revenue": 134000000 }
    ]
  }
}
```

---

## 12. POST /companies/\<id\>/valuations/run — 运行估值计算

> 对应 US-004（P0），需求编号 REQ-M2VAL-004。
> 估值分析页首次进入时可调用，用户调 DCF 参数后再次调用。

### 请求体

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `dcf_discount_rate` | number | 否 | 0.10 | 折现率，范围 0.01~0.30 |
| `dcf_growth_rate` | number | 否 | 0.05 | 永续增长率，范围 0~0.15 |
| `dcf_projection_years` | integer | 否 | 5 | 预测年数，范围 3~10 |

### 成功响应（200）

```json
{
  "traceId": "tr_val_run_001",
  "data": {
    "company_id": "comp_001",
    "methods_computed": 3,
    "methods": ["pe_comparable", "dcf", "pb"],
    "message": "估值计算完成，请查看详情"
  }
}
```

---

## 13. GET /companies/\<id\>/valuations/methods — 各方法估值详情与图表数据

> 对应 US-004（P0），需求编号 REQ-M2VAL-004。
> 用于驱动原型图中的：
> - 目标公司信息卡片
> - PE / DCF / P/B 三个方法卡片
> - 三种估值方法区间对比图
> - 可比公司 PE/PB 散点图
> - DCF 现金流预测图

### 成功响应（200）

| 字段 | 类型 | 必有 | 说明 |
|------|------|------|------|
| `traceId` | string | 是 | 链路追踪 ID |
| `data.company_id` | string | 是 | 目标公司 ID |
| `data.company_name` | string | 是 | 目标公司名称 |
| `data.target_net_profit` | number | 是 | 目标公司净利润（万元） |
| `data.target_net_assets` | number | 是 | 目标公司净资产（万元） |
| `data.comparable_count` | integer | 是 | 可比公司数量 |
| `data.methods` | array | 是 | 各估值方法明细 |
| `data.methods[].method_name` | string | 是 | 方法标识，如 `pe_comparable` |
| `data.methods[].display_name` | string | 是 | 方法显示名称 |
| `data.methods[].valuation_low` | number | 是 | 估值下限（万元） |
| `data.methods[].valuation_mid` | number | 是 | 估值中位数（万元） |
| `data.methods[].valuation_high` | number | 是 | 估值上限（万元） |
| `data.methods[].params` | object | 是 | 方法核心参数 |
| `data.methods[].calculation_detail` | string | 是 | 计算说明 |
| `data.dcf_projection` | object | 否 | DCF 现金流预测图数据 |
| `data.dcf_projection.base_cashflow` | number | 是 | 基期现金流 |
| `data.dcf_projection.discount_rate` | number | 是 | 折现率 |
| `data.dcf_projection.growth_rate` | number | 是 | 永续增长率 |
| `data.dcf_projection.projection_years` | integer | 是 | 预测年数 |
| `data.dcf_projection.yearly_cashflows` | array | 是 | 年度预测结果 |
| `data.dcf_projection.yearly_cashflows[].year` | string | 是 | 年份标签，如 `2026E` |
| `data.dcf_projection.yearly_cashflows[].projected` | number | 是 | 预测现金流 |
| `data.dcf_projection.yearly_cashflows[].discounted` | number | 是 | 折现后现金流 |
| `data.dcf_projection.terminal_value` | number | 是 | 终值 |
| `data.dcf_projection.terminal_value_discounted` | number | 是 | 折现后终值 |
| `data.comparable_scatter` | array | 否 | 可比公司散点图数据 |
| `data.comparable_scatter[].name` | string | 是 | 公司名称 |
| `data.comparable_scatter[].pe` | number | 是 | PE |
| `data.comparable_scatter[].pb` | number | 是 | P/B |
| `data.comparable_scatter[].revenue` | number | 是 | 营收，用于气泡大小 |

### 方法参数说明

#### `pe_comparable`

| 字段 | 类型 | 说明 |
|------|------|------|
| `comparable_pe_median` | number | 可比公司 PE 中位数 |
| `comparable_pe_range` | array<number> | PE 范围 [最小值, 最大值] |
| `comparable_companies` | array<string> | 参与计算的可比公司 |

#### `dcf`

| 字段 | 类型 | 说明 |
|------|------|------|
| `discount_rate` | number | 折现率 |
| `growth_rate` | number | 永续增长率 |
| `projection_years` | integer | 预测年数 |
| `base_cashflow` | number | 基期经营现金流 |

#### `pb`

| 字段 | 类型 | 说明 |
|------|------|------|
| `comparable_pb_median` | number | 可比公司 P/B 中位数 |
| `comparable_pb_range` | array<number> | P/B 范围 [最小值, 最大值] |

### 响应示例

```json
{
  "traceId": "tr_methods_001",
  "data": {
    "company_id": "comp_001",
    "company_name": "字节跳动",
    "target_net_profit": 1200000,
    "target_net_assets": 8000000,
    "comparable_count": 4,
    "methods": [
      {
        "method_name": "pe_comparable",
        "display_name": "PE 可比法",
        "valuation_low": 24000000,
        "valuation_mid": 27000000,
        "valuation_high": 34000000,
        "params": {
          "comparable_pe_median": 22.5,
          "comparable_pe_range": [18.0, 28.3],
          "comparable_companies": ["腾讯控股", "快手科技", "哔哩哔哩", "Meta Platforms"]
        },
        "calculation_detail": "取4家可比公司PE中位数22.5，乘以目标公司净利润1,200,000万元，得估值27,000,000万元"
      },
      {
        "method_name": "dcf",
        "display_name": "DCF 现金流折现法",
        "valuation_low": 20000000,
        "valuation_mid": 25000000,
        "valuation_high": 30000000,
        "params": {
          "discount_rate": 0.10,
          "growth_rate": 0.05,
          "projection_years": 5,
          "base_cashflow": 1500000
        },
        "calculation_detail": "基于经营现金流1,500,000万元，5年预测期，折现率10%，永续增长率5%"
      },
      {
        "method_name": "pb",
        "display_name": "P/B 市净率法",
        "valuation_low": 25600000,
        "valuation_mid": 32000000,
        "valuation_high": 38400000,
        "params": {
          "comparable_pb_median": 4.0,
          "comparable_pb_range": [2.1, 6.5]
        },
        "calculation_detail": "取可比公司PB中位数4.0，乘以目标公司净资产8,000,000万元，得估值32,000,000万元"
      }
    ],
    "dcf_projection": {
      "base_cashflow": 1500000,
      "discount_rate": 0.10,
      "growth_rate": 0.05,
      "projection_years": 5,
      "yearly_cashflows": [
        { "year": "2026E", "projected": 1575000, "discounted": 1431818 },
        { "year": "2027E", "projected": 1653750, "discounted": 1368760 },
        { "year": "2028E", "projected": 1736438, "discounted": 1308728 },
        { "year": "2029E", "projected": 1823259, "discounted": 1251598 },
        { "year": "2030E", "projected": 1914422, "discounted": 1197227 }
      ],
      "terminal_value": 38288448,
      "terminal_value_discounted": 23775000
    },
    "comparable_scatter": [
      { "name": "腾讯控股", "pe": 22.5, "pb": 4.8, "revenue": 55000000 },
      { "name": "快手科技", "pe": 28.3, "pb": 3.2, "revenue": 11000000 },
      { "name": "哔哩哔哩", "pe": 35.2, "pb": 2.1, "revenue": 6500000 },
      { "name": "Meta Platforms", "pe": 18.8, "pb": 6.5, "revenue": 134000000 }
    ]
  }
}
```

---

## 14. GET /companies/\<id\>/valuations/summary — 估值结果综合摘要

> 对应 US-005（P0），需求编号 REQ-M2VAL-005。
> 用于驱动原型图中的：
> - 估值中枢大数字
> - 各方法摘要表
> - AI 推荐卡片与置信度进度条
> - 估值区间图
> - 方法权重饼图
> - 敏感性分析图
> - 可信度评分图

### 成功响应（200）

| 字段 | 类型 | 必有 | 说明 |
|------|------|------|------|
| `traceId` | string | 是 | 链路追踪 ID |
| `data.company_id` | string | 是 | 目标公司 ID |
| `data.company_name` | string | 是 | 目标公司名称 |
| `data.valuation_center` | number | 是 | 估值中枢（万元） |
| `data.valuation_range_low` | number | 是 | 综合区间下限（万元） |
| `data.valuation_range_high` | number | 是 | 综合区间上限（万元） |
| `data.methods_summary` | array | 是 | 各方法摘要 |
| `data.methods_summary[].method_name` | string | 是 | 方法标识 |
| `data.methods_summary[].display_name` | string | 是 | 方法显示名称 |
| `data.methods_summary[].valuation_low` | number | 是 | 方法区间下限（万元） |
| `data.methods_summary[].valuation_mid` | number | 是 | 方法中位数（万元） |
| `data.methods_summary[].valuation_high` | number | 是 | 方法区间上限（万元） |
| `data.methods_summary[].valuation_range` | string | 是 | 展示文案，如 `2.4万亿 ~ 3.4万亿` |
| `data.methods_summary[].weight` | number | 是 | 方法权重，单位 % |
| `data.ai_recommendation` | object | 是 | AI 推荐摘要 |
| `data.ai_recommendation.recommended_method` | string | 是 | 推荐方法 |
| `data.ai_recommendation.reason` | string | 是 | 推荐理由 |
| `data.ai_recommendation.summary` | string | 是 | 综合说明 |
| `data.ai_recommendation.confidence` | number | 是 | 置信度，0~100 |
| `data.sensitivity_analysis` | object | 是 | 敏感性分析图数据 |
| `data.sensitivity_analysis.discount_rates` | array<number> | 是 | 折现率刻度，单位 % |
| `data.sensitivity_analysis.scenarios` | array | 是 | 多增长率情景 |
| `data.sensitivity_analysis.scenarios[].growth_rate` | number | 是 | 增长率，单位 % |
| `data.sensitivity_analysis.scenarios[].valuations` | array<number> | 是 | 对应估值结果，单位万亿 |
| `data.confidence_scores` | array | 是 | 各方法可信度评分 |
| `data.confidence_scores[].method_name` | string | 是 | 方法标识 |
| `data.confidence_scores[].display_name` | string | 是 | 方法显示名称 |
| `data.confidence_scores[].data_quality` | number | 是 | 数据质量评分 |
| `data.confidence_scores[].method_applicability` | number | 是 | 方法适用性评分 |
| `data.confidence_scores[].sample_sufficiency` | number | 是 | 样本充足度评分 |

### 响应示例

```json
{
  "traceId": "tr_summary_001",
  "data": {
    "company_id": "comp_001",
    "company_name": "字节跳动",
    "valuation_center": 28000000,
    "valuation_range_low": 20000000,
    "valuation_range_high": 38400000,
    "methods_summary": [
      {
        "method_name": "pe_comparable",
        "display_name": "PE 可比法",
        "valuation_low": 24000000,
        "valuation_mid": 27000000,
        "valuation_high": 34000000,
        "valuation_range": "2.4万亿 ~ 3.4万亿",
        "weight": 40
      },
      {
        "method_name": "dcf",
        "display_name": "DCF 法",
        "valuation_low": 20000000,
        "valuation_mid": 25000000,
        "valuation_high": 30000000,
        "valuation_range": "2.0万亿 ~ 3.0万亿",
        "weight": 35
      },
      {
        "method_name": "pb",
        "display_name": "P/B 法",
        "valuation_low": 25600000,
        "valuation_mid": 32000000,
        "valuation_high": 38400000,
        "valuation_range": "2.56万亿 ~ 3.84万亿",
        "weight": 25
      }
    ],
    "ai_recommendation": {
      "recommended_method": "PE可比法",
      "reason": "目标公司处于成熟期互联网行业，盈利稳定，PE可比法最能反映市场对该行业的估值共识",
      "summary": "综合三种估值方法，字节跳动估值中枢约2.8万亿元。考虑到公司盈利能力稳定且可比公司样本充足，PE可比法最具参考价值。DCF法受折现率假设影响较大，P/B法因轻资产属性偏高，建议以PE法为锚。",
      "confidence": 82
    },
    "sensitivity_analysis": {
      "discount_rates": [8, 9, 10, 11, 12, 13, 14],
      "scenarios": [
        { "growth_rate": 3, "valuations": [3.10, 2.85, 2.60, 2.40, 2.22, 2.08, 1.95] },
        { "growth_rate": 5, "valuations": [3.50, 3.15, 2.85, 2.60, 2.40, 2.22, 2.08] },
        { "growth_rate": 7, "valuations": [4.10, 3.60, 3.20, 2.88, 2.62, 2.40, 2.22] }
      ]
    },
    "confidence_scores": [
      { "method_name": "pe_comparable", "display_name": "PE 可比法", "data_quality": 90, "method_applicability": 85, "sample_sufficiency": 88 },
      { "method_name": "dcf", "display_name": "DCF 法", "data_quality": 75, "method_applicability": 80, "sample_sufficiency": 70 },
      { "method_name": "pb", "display_name": "P/B 法", "data_quality": 70, "method_applicability": 60, "sample_sufficiency": 72 }
    ]
  }
}
```

---

## 15. 参数校验规则汇总

| 端点 | 字段 | 规则 | 失败 HTTP | error.code |
|------|------|------|-----------|-----------|
| GET /companies | `page_size` | 1~100 | 400 | `INVALID_PARAMS` |
| GET /companies/<id>/comparables/candidates | `limit` | 1~50 | 400 | `INVALID_PARAMS` |
| PUT /companies/<id>/comparables | `comparable_ids` | 数组长度 1~10 | 400 | `INVALID_PARAMS` |
| POST /companies/<id>/valuations/run | 前置条件 | 必须已确认可比公司 | 400 | `NO_COMPARABLES` |
| POST /companies/<id>/valuations/run | `dcf_discount_rate` | 0.01~0.30 | 400 | `INVALID_PARAMS` |
| POST /companies/<id>/valuations/run | `dcf_growth_rate` | 0~0.15 | 400 | `INVALID_PARAMS` |
| POST /companies/<id>/valuations/run | `dcf_projection_years` | 3~10 | 400 | `INVALID_PARAMS` |
| 所有含 `<id>` 的接口 | `id` | 公司必须存在 | 404 | `COMPANY_NOT_FOUND` |
| GET /companies/<id>/financials | — | 后端无预置财务数据时返回 | 404 | `FINANCIALS_NOT_FOUND` |
| GET /valuations/methods | — | 必须先运行估值 | 404 | `VALUATION_NOT_FOUND` |
| GET /valuations/summary | — | 必须先运行估值 | 404 | `VALUATION_NOT_FOUND` |

---

## 16. 页面与接口映射表

> 本节用于帮助前端、后端、测试三方快速对齐。

| 页面 | 页面模块 | 调用接口 | 关键字段 |
|------|----------|----------|----------|
| 公司列表 | 搜索结果表格 | `GET /companies` | `companies[]` |
| 公司列表 | 顶部统计卡片 | `GET /statistics` | `total_companies` `valued_companies` `valued_ratio` `total_industries` `industry_groups` `weekly_new_companies` `weekly_new_delta` |
| 公司列表 | 行业分布图 | `GET /statistics` | `industry_distribution[]` |
| 公司列表 | 估值状态图 | `GET /statistics` | `valuation_status` |
| 公司列表 | 各行业平均 PE 图 | `GET /statistics` | `industry_avg_pe[]` |
| 公司详情 | 基本信息 | `GET /companies/<id>` | `name` `industry` `founded_year` `description` |
| 公司详情 | 行业概况 | `GET /companies/<id>` | `industry_info.avg_pe` `industry_info.growth_rate` `industry_info.company_count` |
| 公司详情 | 行业 PE 分布 | `GET /companies/<id>` | `industry_info.pe_distribution[]` |
| 公司详情 | 财务卡片 | `GET /companies/<id>/financials` | `latest_summary.*` |
| 公司详情 | 财务表格 | `GET /companies/<id>/financials` | `financials[]` |
| 公司详情 | 财务比率雷达图 | `GET /companies/<id>/financials` | `ratios` `industry_avg_ratios` |
| 可比公司 | AI 推荐卡片 | `POST /companies/<id>/comparables/recommend` | `recommendations[]` |
| 可比公司 | 相似度雷达图 | `POST /companies/<id>/comparables/recommend` | `recommendations[].similarity_dimensions` |
| 可比公司 | 手动添加公司弹层/搜索 | `GET /companies/<id>/comparables/candidates` | `candidates[]` |
| 可比公司 | 可比公司表格 | `GET /companies/<id>/comparables` | `comparables[]` |
| 估值分析 | 方法卡片 | `GET /companies/<id>/valuations/methods` | `methods[]` |
| 估值分析 | DCF 预测图 | `GET /companies/<id>/valuations/methods` | `dcf_projection` |
| 估值分析 | 散点图 | `GET /companies/<id>/valuations/methods` | `comparable_scatter[]` |
| 估值结果 | 综合摘要 | `GET /companies/<id>/valuations/summary` | `valuation_center` `methods_summary[]` `ai_recommendation` |
| 估值结果 | 权重图 | `GET /companies/<id>/valuations/summary` | `methods_summary[].weight` |
| 估值结果 | 敏感性分析图 | `GET /companies/<id>/valuations/summary` | `sensitivity_analysis` |
| 估值结果 | 可信度图 | `GET /companies/<id>/valuations/summary` | `confidence_scores[]` |

---

## 17. 需求追溯总索引

| 需求编号 | UserStory | 优先级 | →09 接口 |
|----------|-----------|--------|----------|
| REQ-M2VAL-001 | 目标公司选择与筛选 | P0 | `GET /companies` `GET /statistics` |
| REQ-M2VAL-002 | 目标公司详情与财务数据 | P0 | `GET /companies/<id>` `GET /companies/<id>/financials` |
| REQ-M2VAL-003 | 可比公司 AI 推荐与确认 | P0 | `POST /companies/<id>/comparables/recommend` `GET /companies/<id>/comparables/candidates` `PUT /companies/<id>/comparables` `GET /companies/<id>/comparables` |
| REQ-M2VAL-004 | 多方法估值分析 | P0 | `POST /companies/<id>/valuations/run` `GET /companies/<id>/valuations/methods` |
| REQ-M2VAL-005 | 估值结果综合展示 | P0 | `GET /companies/<id>/valuations/summary` |

---

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-04-14 | 首版填写，定义基础估值流程接口 |
| v0.2 | 2026-04-15 | 基于原型图重写：新增 `/statistics`；扩展详情、财务、推荐、估值方法、结果摘要字段；补齐图表和摘要所需数据契约 |
| v0.2.1 | 2026-04-15 | 交叉检验补漏：补充手动添加可比公司候选接口、结果导出接口、统计卡片副文案字段，以及财务导入支持 CSV/JSON 的说明 |
| v0.2.2 | 2026-04-15 | 按 demo 范围收缩：删除财务导入与结果导出接口，改为前端选中公司后由后端自动返回预置财务数据和结果 |
