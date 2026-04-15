"""JSON 文件读写工具（线程安全）"""
import json
import os
import threading

_lock = threading.Lock()


def read_json(filepath):
    """读取 JSON 文件"""
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return []
        return json.loads(content)


def write_json(filepath, data):
    """写入 JSON 文件（线程安全）"""
    with _lock:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
