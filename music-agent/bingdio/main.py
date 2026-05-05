"""Bingody — CLI 个人 AI 音乐智能体 入口"""

import logging
import sys
from pathlib import Path

# 确保项目根目录在 path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("bingdio")


def run():
    """启动 B-mode 自主规划智能体"""
    from bingdio.main_b import run as run_b
    run_b()


if __name__ == "__main__":
    run()