"""
价格采集服务测试。

使用 2025-12-01 (基准日期) 的数据进行验证，
对比投资跟踪表格中的基准价格，确认数据源可用且价格合理。
"""

import sys
from src.services.price_fetcher import fetch_price, fetch_all_prices

# 基准日期和表格中的基准价格（来自投资跟踪表格.xlsx）
BASE_DATE = "2025-12-01"
EXPECTED_PRICES = {
    "GOOGL": 313,
    "AMZN": 233.88,
    "META": 640.87,
    "AAPL": 283.1,
    "NVDA": 179.91,
    "0700.HK": 619.5,
    "BABA": 164.26,
    "BTC-USD": 86309.1,
    "AU9999": 958.46,
    "^TNX": 4.0962,
    "CN10Y": 1.827,
}

# 允许的价格偏差范围（百分比），用于模糊匹配
# 因为"12月1日"可能不是交易日，实际取到的是附近交易日的价格
TOLERANCE_PERCENT = 5.0


def test_single_fetch():
    """测试单个标的价格获取（以 GOOGL 为例）。"""
    price = fetch_price("GOOGL", BASE_DATE)
    assert price is not None, "GOOGL 价格获取失败"
    print(f"[PASS] GOOGL 单标的获取成功: {price:.2f}")


def test_all_tickers():
    """测试所有标的的价格获取，并与基准价格对比。"""
    tickers = list(EXPECTED_PRICES.keys())
    results = fetch_all_prices(tickers, BASE_DATE)

    pass_count = 0
    fail_count = 0

    print("\n--- 价格对比结果 ---")
    for ticker, expected in EXPECTED_PRICES.items():
        actual = results.get(ticker)
        if actual is None:
            print(f"[FAIL] {ticker}: 获取失败")
            fail_count += 1
            continue

        # 计算偏差百分比
        deviation = abs(actual - expected) / expected * 100
        status = "PASS" if deviation < TOLERANCE_PERCENT else "WARN"
        if status == "PASS":
            pass_count += 1
        else:
            fail_count += 1

        print(
            f"[{status}] {ticker}: "
            f"期望={expected}, 实际={actual:.4f}, "
            f"偏差={deviation:.2f}%"
        )

    print(f"\n结果: {pass_count} 通过, {fail_count} 失败/偏差过大")
    assert fail_count == 0, f"{fail_count} 个标的获取失败或偏差过大"


def test_unknown_ticker():
    """测试未知标的代码的处理。"""
    price = fetch_price("UNKNOWN_TICKER_XYZ", BASE_DATE)
    assert price is None, "未知标的应返回 None"
    print("[PASS] 未知标的正确返回 None")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("=== 测试单标的获取 ===")
    test_single_fetch()
    print("\n=== 测试所有标的获取 ===")
    test_all_tickers()
    print("\n=== 测试未知标的 ===")
    test_unknown_ticker()
    print("\n全部测试完成!")
