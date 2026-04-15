---
description: 大模型对接相关规范
trigger: always_on
---
## 大模型对接规范

### 使用百炼平台
在对接大模型时，统一使用阿里云百炼平台（DashScope）。

- **API Key**: `sk-f47c2e9de62c4375800379e938e2c25b`
- **平台文档**: https://dashscope.aliyuncs.com
- **数据来源**: 使用网上公开数据作为数据源

### 示例代码（Python）
import dashscope
from dashscope import Generation

dashscope.api_key = "sk-f47c2e9de62c4375800379e938e2c25b"

response = Generation.call(
    model="qwen-turbo",
    messages=[{"role": "user", "content": "your prompt here"}]
)
print(response.output.text)

### 示例代码（HTTP）
POST https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation
Authorization: Bearer sk-f47c2e9de62c4375800379e938e2c25b
Content-Type: application/json

### 注意事项
- API Key 请勿提交至代码仓库，建议通过环境变量注入
- 数据源优先选用公开金融数据平台（如 akshare、tushare 公开接口等）
