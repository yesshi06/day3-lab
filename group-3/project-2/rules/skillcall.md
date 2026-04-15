# 后端编程 Skill 调用规范

## 基本原则

在进行后端编程时，**必须优先调用** `financial-analysis` 目录下提供的各种金融专业 skills，避免重复造轮子。

---

## 可用 Skills 目录

在编写后端逻辑前，请先浏览 `financial-analysis` 目录，了解已有的 skill 列表，例如：

- 股票行情分析 skill
- 基金净值查询 skill
- 财务指标计算 skill
- 风险评估 skill
- 市场趋势分析 skill

---

## 调用方式示例

# 示例：调用 financial-analysis 中的 skill
from financial_analysis.skills import stock_analysis, fund_nav, risk_assessment

# 调用股票分析 skill
result = stock_analysis.run(symbol="600519", period="1y")

# 调用基金净值查询 skill
nav_data = fund_nav.run(fund_code="110022")

# 调用风险评估 skill
risk_result = risk_assessment.run(portfolio=portfolio_data)

---

## 调用流程

1. **查阅 skill 列表**：先查看 `financial-analysis/skills/` 目录下已有哪些可用的 skill
2. **优先复用**：如果已有 skill 能满足需求，直接调用，不要重新实现
3. **参数确认**：调用前确认 skill 所需的输入参数格式与数据类型
4. **结果处理**：根据 skill 返回的数据结构进行后续业务逻辑处理
5. **缺失时新增**：若无合适 skill，需在 `financial-analysis/skills/` 中新建，并遵循统一规范

---

## 注意事项

- 所有金融数据获取类操作，**必须通过 skill 封装**，不得在业务层直接调用第三方 API
- skill 调用出错时，需做好异常捕获与降级处理
- 新增或修改 skill 后，需同步更新对应的文档说明
- 数据源优先选用公开金融数据平台（如 `akshare`、`tushare` 公开接口等）
