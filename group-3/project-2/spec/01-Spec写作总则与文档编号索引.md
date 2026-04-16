# 01 — Spec 写作总则 & 文档编号索引

---

| 项 | 值 |
|---|---|
| 模块编号 | M2-VAL |
| 模块名称 | 公司估值系统 |
| 文档版本 | v0.1 |
| 文档状态 | Draft |

---

## 一、编号与阶段对照（00 ~ 14）

| 编号 | 阶段 | 分类 | 文档名称 |
|------|------|------|----------|
| `01` | Meta | 编号规范 | Spec 写作总则与文档编号索引 |
| `02` | Meta | Elicitation | 需求来源与采集记录 |
| `03` | Proposal | Proposal | 立项提案与范围说明 |
| `04` | Proposal | PRD | 产品需求说明 |
| `05` | Spec | UserStory | 用户故事与验收标准 |
| `06` | Spec | FSD | 功能规格说明 |
| `07` | Spec | NFR | 非功能需求与约束 |
| `08` | Design | Architecture | 系统架构与技术选型 |
| `09` | Design | API | 接口规格（契约真源） |
| `10` | Design | Data | 数据模型与存储规格 |
| `11` | Design | Security | 安全设计规格 |
| `12` | Plan | Plan | 实施计划与里程碑 |
| `13` | Test | Test | 测试策略与质量门禁 |
| `14` | Trace | Traceability | 需求追踪矩阵（四向对齐） |

## 二、基本原则

1. **单一真相**：对外行为以 `09` API 与 `10` 数据模型为准
2. **先行为后实现**：先定义 `05` 用户故事，再写 `06/09/10`
3. **可验证**：所有 MUST 条目必须能被测试或监控验证
4. **不混层**：PRD 不写 SQL，API 不写像素，Test 不重复规则
5. **无歧义**：禁止「可选其一 / 建议 / 大概 / 尽量」等表述

## 三、规范词（RFC 风格）

| 词 | 含义 |
|----|------|
| **MUST** | 必须，违反即缺陷 |
| **SHOULD** | 建议，不满足需说明理由 |
| **MAY** | 可选，不影响基线验收 |
| **MUST NOT** | 严禁 |

## 四、术语表（Glossary）

| 缩写 | 英文全称 | 中文含义 |
|------|----------|----------|
| **PE** | Price-to-Earnings Ratio | 市盈率 |
| **DCF** | Discounted Cash Flow | 现金流折现法 |
| **EPS** | Earnings Per Share | 每股收益 |
| **P/B** | Price-to-Book Ratio | 市净率 |
| **EV/EBITDA** | Enterprise Value / EBITDA | 企业价值倍数 |
| **三表** | Three Financial Statements | 资产负债表+利润表+现金流量表 |
| **可比公司** | Comparable Companies | 行业内用于估值参照的上市公司 |
| **目标公司** | Target Company | 待估值的公司 |

## 五、六阶段流程

```
Proposal(03-04) → Spec(05-06-07) → Design(08-09-10-11) → Plan(12) → Test(13) → Trace(14)
  Why              What              How             When/Who     OK?      All linked?
```

## 六、源码目录参考

```
M2-VAL/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # Flask 应用入口
│   │   ├── config.py            # 配置
│   │   ├── models/              # 数据模型
│   │   ├── services/            # 业务编排层
│   │   ├── routers/             # API 路由
│   │   ├── storage.py           # Storage 层 — JSON CRUD
│   │   └── utils/
│   ├── data/                    # JSON 数据文件
│   └── tests/
├── frontend/
│   └── src/
│       ├── App.jsx              # 主组件
│       ├── pages/               # 5 个核心页面
│       └── App.css
├── M2-VAL-specs/                # 本规格文档目录
└── README.md
```

---

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-04-14 | 首版填写 |
