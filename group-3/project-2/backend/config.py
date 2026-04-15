"""应用全局配置"""
import os

# 阿里云百炼平台 DashScope API Key
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "sk-f47c2e9de62c4375800379e938e2c25b")

# DashScope 模型
DASHSCOPE_MODEL = "qwen-turbo"

# JSON 数据文件目录
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Flask 服务端口
PORT = 5000

# 分页默认值
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# 估值方法权重
WEIGHT_PE = 40
WEIGHT_DCF = 35
WEIGHT_PB = 25

# DCF 默认参数
DCF_DEFAULT_DISCOUNT_RATE = 0.10
DCF_DEFAULT_GROWTH_RATE = 0.05
DCF_DEFAULT_PROJECTION_YEARS = 5
