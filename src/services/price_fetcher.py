"""
价格数据采集模块。

负责从不同数据源获取各类投资标的的收盘价。
- 美股 / 港股 / 中概 / 加密货币 / 美国国债：通过 yfinance 获取
- AU9999 黄金：通过 akshare 获取（上海黄金交易所）
- 中国国债收益率：通过 akshare 获取（中债收益率曲线）
"""

from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import yfinance as yf
import akshare as ak


# ============================================================
# 数据源分类配置
# 根据标的类型选择不同的数据获取方式
# ============================================================

# 通过 yfinance 获取的标的（美股、港股、中概、加密货币、美国国债）
YFINANCE_TICKERS = {
    "GOOGL", "AMZN", "META", "AAPL", "NVDA",  # 美股
    "0700.HK",                                    # 港股
    "BABA",                                        # 中概
    "BTC-USD",                                     # 加密货币
    "^TNX",                                        # 10年期美国国债收益率
}

# 通过 akshare 获取的标的（需要特殊处理）
AKSHARE_GOLD = "AU9999"       # 上海黄金交易所黄金
AKSHARE_CN_BOND = "CN10Y"     # 10年期中国国债收益率


def fetch_price(ticker: str, target_date: str) -> Optional[float]:
    """
    获取指定标的在指定日期的收盘价。

    这是对外的统一入口，内部根据 ticker 类型分发到不同的数据源。

    Args:
        ticker: 标的交易代码，如 "GOOGL"、"AU9999"、"CN10Y"。
        target_date: 目标日期，格式 "YYYY-MM-DD"。
                     会自动查找该日期当天或之前最近一个交易日的收盘价。

    Returns:
        收盘价（float），获取失败时返回 None。
    """
    if ticker == AKSHARE_GOLD:
        return _fetch_gold_price(target_date)
    elif ticker == AKSHARE_CN_BOND:
        return _fetch_cn_bond_yield(target_date)
    elif ticker in YFINANCE_TICKERS:
        return _fetch_yfinance_price(ticker, target_date)
    else:
        print(f"[警告] 未知的标的代码: {ticker}")
        return None


def fetch_all_prices(
    tickers: list[str], target_date: str
) -> dict[str, Optional[float]]:
    """
    批量获取多个标的在指定日期的收盘价。

    Args:
        tickers: 标的代码列表。
        target_date: 目标日期，格式 "YYYY-MM-DD"。

    Returns:
        字典，key 为 ticker，value 为收盘价或 None。
    """
    results = {}
    for ticker in tickers:
        price = fetch_price(ticker, target_date)
        results[ticker] = price
        status = f"{price:.4f}" if price is not None else "获取失败"
        print(f"  [{ticker}] {status}")
    return results


# ============================================================
# 内部实现：yfinance 数据获取
# ============================================================

def _fetch_yfinance_price(ticker: str, target_date: str) -> Optional[float]:
    """
    通过 yfinance 获取指定标的的收盘价。

    会查找 target_date 当天或之前最近交易日的数据。
    搜索范围为 target_date 前 10 天，以覆盖周末和节假日。

    Args:
        ticker: yfinance 支持的交易代码。
        target_date: 目标日期，格式 "YYYY-MM-DD"。

    Returns:
        收盘价（float），失败返回 None。
    """
    try:
        target = datetime.strptime(target_date, "%Y-%m-%d")
        # 向前多取 10 天数据，确保能找到最近的交易日
        start = target - timedelta(days=10)
        end = target + timedelta(days=1)  # yfinance 的 end 是开区间

        t = yf.Ticker(ticker)
        hist = t.history(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"))

        if hist.empty:
            print(f"[警告] {ticker} 在 {target_date} 附近无数据")
            return None

        # 取最后一条记录（即 target_date 当天或之前最近的交易日）
        return float(hist["Close"].iloc[-1])
    except Exception as e:
        print(f"[错误] 获取 {ticker} 价格失败: {e}")
        return None


# ============================================================
# 内部实现：AU9999 黄金价格（akshare）
# ============================================================

def _fetch_gold_price(target_date: str) -> Optional[float]:
    """
    通过 akshare 获取上海黄金交易所 Au99.99 的收盘价。

    数据单位：人民币元/克。

    Args:
        target_date: 目标日期，格式 "YYYY-MM-DD"。

    Returns:
        收盘价（float），失败返回 None。
    """
    try:
        # akshare 接口返回完整历史数据
        df = ak.spot_hist_sge(symbol="Au99.99")

        # 确保日期列为 datetime 类型
        df["date"] = pd.to_datetime(df["date"])
        target = pd.Timestamp(target_date)

        # 筛选 target_date 当天及之前的数据，取最近一条
        df_before = df[df["date"] <= target]
        if df_before.empty:
            print(f"[警告] AU9999 在 {target_date} 之前无数据")
            return None

        return float(df_before.iloc[-1]["close"])
    except Exception as e:
        print(f"[错误] 获取 AU9999 黄金价格失败: {e}")
        return None


# ============================================================
# 内部实现：中国10年期国债收益率（akshare）
# ============================================================

def _fetch_cn_bond_yield(target_date: str) -> Optional[float]:
    """
    通过 akshare 获取中债国债收益率曲线中的10年期收益率。

    数据单位：百分比（如 1.827 表示 1.827%）。

    Args:
        target_date: 目标日期，格式 "YYYY-MM-DD"。

    Returns:
        10年期收益率（float），失败返回 None。
    """
    try:
        target = datetime.strptime(target_date, "%Y-%m-%d")
        # akshare 接口要求日期范围不超过一年，且格式为 YYYYMMDD
        start = target - timedelta(days=30)
        start_str = start.strftime("%Y%m%d")
        end_str = target.strftime("%Y%m%d")

        df = ak.bond_china_yield(start_date=start_str, end_date=end_str)

        # 筛选"中债国债收益率曲线"
        df = df[df["曲线名称"] == "中债国债收益率曲线"]
        if df.empty:
            print(f"[警告] 中国国债收益率在 {target_date} 附近无数据")
            return None

        # 确保日期列为 datetime 类型，筛选 target_date 当天或之前
        df["日期"] = pd.to_datetime(df["日期"])
        df_before = df[df["日期"] <= pd.Timestamp(target_date)]
        if df_before.empty:
            print(f"[警告] 中国国债收益率在 {target_date} 之前无数据")
            return None

        # 取最近一条的10年期收益率
        return float(df_before.iloc[-1]["10年"])
    except Exception as e:
        print(f"[错误] 获取中国国债收益率失败: {e}")
        return None
