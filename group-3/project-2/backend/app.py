"""Flask 应用入口"""
import logging
import os
import sys
from datetime import datetime
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from routes.companies import companies_bp
from routes.financials import financials_bp
from routes.comparables import comparables_bp
from routes.valuations import valuations_bp
from services.data_sync import sync_all
import config

# 日志文件路径
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server.log")


def create_app():
    app = Flask(__name__)
    CORS(app)

    # 配置日志输出到 stdout（确保终端可见）
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    ))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    prefix = "/api/v1/valuation"
    app.register_blueprint(companies_bp, url_prefix=prefix)
    app.register_blueprint(financials_bp, url_prefix=prefix)
    app.register_blueprint(comparables_bp, url_prefix=prefix)
    app.register_blueprint(valuations_bp, url_prefix=prefix)

    @app.before_request
    def log_request_start():
        g.start_time = datetime.now()

    @app.after_request
    def log_request_end(response):
        duration = (datetime.now() - g.start_time).total_seconds() * 1000
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{ts}] {request.method} {request.path} -> {response.status_code} ({duration:.0f}ms)\n"
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_line)
        return response

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "module": "M2-VAL"})

    @app.route("/api/v1/valuation/sync", methods=["POST"])
    def manual_sync():
        """POST /api/v1/valuation/sync — 手动触发数据同步"""
        result = sync_all()
        return jsonify({"status": "ok", "sync_result": result})

    return app


if __name__ == "__main__":
    # 清空旧日志
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"=== M2-VAL 后端服务启动 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    # 启动时自动同步数据
    print("\n[DataSync] 启动时同步上市公司数据...")
    sys.stdout.flush()
    try:
        sync_all()
    except Exception as e:
        print(f"[DataSync] 同步失败，使用缓存数据: {e}")

    app = create_app()
    print(f"\n=== M2-VAL 后端服务启动 ===")
    print(f"地址: http://127.0.0.1:{config.PORT}")
    print(f"日志文件: {LOG_FILE}")
    print(f"数据源: 腾讯财经 API (实时行情)")
    print("=" * 30 + "\n")
    sys.stdout.flush()
    app.run(host="0.0.0.0", port=config.PORT, debug=True)
