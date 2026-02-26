"""
数据库初始化与连接管理模块。

使用 SQLite 作为本地数据存储，提供统一的数据库连接和表结构初始化功能。
"""

import sqlite3
import os
from pathlib import Path


# 默认数据库文件路径：项目根目录下的 data/invest.db
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "invest.db"


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    """
    获取数据库连接。

    Args:
        db_path: 数据库文件路径，为 None 时使用默认路径。

    Returns:
        sqlite3.Connection: 数据库连接对象，已启用外键约束。
    """
    if db_path is None:
        db_path = str(DEFAULT_DB_PATH)

    # 确保数据库所在目录存在
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    # 启用外键约束（SQLite 默认关闭）
    conn.execute("PRAGMA foreign_keys = ON")
    # 返回字典形式的查询结果，方便使用
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str | None = None) -> None:
    """
    初始化数据库，创建所有表结构。

    如果表已存在则跳过（CREATE TABLE IF NOT EXISTS）。
    可安全重复调用。

    Args:
        db_path: 数据库文件路径，为 None 时使用默认路径。
    """
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()


# ============================================================
# 数据库表结构定义
# ============================================================

SCHEMA_SQL = """
-- ============================================================
-- 投资标的表
-- 记录所有被跟踪的投资标的基本信息。
-- 每个标的有唯一的交易代码（ticker），如 GOOGL、BTC-USD。
-- ============================================================
CREATE TABLE IF NOT EXISTS assets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,                        -- 标的名称，如 "Google"
    ticker      TEXT    NOT NULL UNIQUE,                 -- 交易代码，如 "GOOGL"（用于 API 查询）
    asset_type  TEXT    NOT NULL,                        -- 资产类别：美股 / 港股 / 中概 / 大宗商品 / 债券 / 加密货币
    base_price  REAL    NOT NULL,                        -- 基准价格（首次录入时的价格）
    base_date   TEXT    NOT NULL,                        -- 基准日期，如 "2025-12-01"
    is_active   INTEGER NOT NULL DEFAULT 1,              -- 是否活跃跟踪：1=是, 0=否
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))  -- 创建时间
);

-- ============================================================
-- 月度价格记录表
-- 每月2日自动采集上月末收盘价，存入此表。
-- 同一标的同一日期只允许一条记录（UNIQUE 约束）。
-- ============================================================
CREATE TABLE IF NOT EXISTS monthly_prices (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id    INTEGER NOT NULL,                        -- 关联的标的 ID
    record_date TEXT    NOT NULL,                        -- 记录日期，如 "2026-01-01"（代表该月的数据）
    close_price REAL    NOT NULL,                        -- 收盘价
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (asset_id) REFERENCES assets(id),
    UNIQUE(asset_id, record_date)                        -- 同一标的同一日期不允许重复
);

-- ============================================================
-- 持仓表
-- 记录每个标的当前的累计投入金额。
-- 每个标的只有一条记录，通过 position_changes 表的变动来更新。
-- ============================================================
CREATE TABLE IF NOT EXISTS positions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id        INTEGER NOT NULL UNIQUE,              -- 关联的标的 ID（一对一）
    total_invested  REAL    NOT NULL DEFAULT 0,           -- 累计投入金额（美元）
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now')),  -- 最后更新时间
    FOREIGN KEY (asset_id) REFERENCES assets(id)
);

-- ============================================================
-- 仓位变动记录表
-- 每次加仓或减仓都会记录一条日志，用于追溯资金变动历史。
-- 这是审计表，只增不改不删。
-- ============================================================
CREATE TABLE IF NOT EXISTS position_changes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id        INTEGER NOT NULL,                     -- 关联的标的 ID
    change_type     TEXT    NOT NULL,                     -- 变动类型："加仓" 或 "减仓"
    amount          REAL    NOT NULL,                     -- 变动金额（美元），始终为正数
    price_at_change REAL,                                 -- 变动时的标的价格（可选，供参考）
    change_date     TEXT    NOT NULL,                     -- 变动日期，如 "2026-03-15"
    note            TEXT,                                 -- 备注说明，如 "定投加仓"
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (asset_id) REFERENCES assets(id)
);
"""
