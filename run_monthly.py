"""
月度定时任务入口脚本。

供 cron 定时任务调用。
在云服务器上配置 crontab：
    0 9 2 * * cd /path/to/invest_anget && python run_monthly.py
    含义：每月2日上午9点执行

也可手动运行，支持指定日期：
    python run_monthly.py                  # 自动取当月
    python run_monthly.py 2026-01-01       # 指定月份
"""

import sys
import os

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.monthly_job import run_monthly_job

if __name__ == "__main__":
    target_date = sys.argv[1] if len(sys.argv) > 1 else None
    success = run_monthly_job(target_date)
    sys.exit(0 if success else 1)
