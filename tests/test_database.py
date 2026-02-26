"""数据库初始化测试。"""

import sqlite3
import os
import tempfile
from src.models.database import get_connection, init_db


def test_init_db():
    """测试数据库初始化：所有表是否正确创建。"""
    # 使用临时文件，避免污染正式数据库
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        init_db(db_path)
        conn = get_connection(db_path)

        # 查询所有用户创建的表名（排除 SQLite 内部表）
        cursor = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        tables = [row["name"] for row in cursor.fetchall()]
        conn.close()

        expected_tables = ["assets", "monthly_prices", "position_changes", "positions"]
        assert tables == expected_tables, f"期望表: {expected_tables}, 实际表: {tables}"
        print("[PASS] 所有表创建成功:", tables)
    finally:
        os.unlink(db_path)


def test_init_db_idempotent():
    """测试数据库初始化的幂等性：重复调用不报错。"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        init_db(db_path)
        init_db(db_path)  # 第二次调用不应报错
        print("[PASS] 重复初始化无报错")
    finally:
        os.unlink(db_path)


def test_foreign_keys_enabled():
    """测试外键约束是否生效。"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        init_db(db_path)
        conn = get_connection(db_path)

        # 尝试插入一条引用不存在 asset_id 的价格记录，应该报错
        try:
            conn.execute(
                "INSERT INTO monthly_prices (asset_id, record_date, close_price) "
                "VALUES (999, '2026-01-01', 100.0)"
            )
            conn.commit()
            assert False, "外键约束未生效，不应允许插入"
        except sqlite3.IntegrityError:
            print("[PASS] 外键约束生效")
        finally:
            conn.close()
    finally:
        os.unlink(db_path)


if __name__ == "__main__":
    test_init_db()
    test_init_db_idempotent()
    test_foreign_keys_enabled()
    print("\n全部测试通过！")
