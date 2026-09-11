"""SQLite 数据库模块：存储检测记录与统计。"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "inspection.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS inspection_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    image_name TEXT,
    defect_class TEXT NOT NULL,
    confidence REAL,
    severity TEXT NOT NULL,
    defect_area_ratio REAL,
    bbox TEXT,
    raw_features TEXT
);
"""


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    return conn


def insert_record(image_name, defect_class, confidence, severity,
                  defect_area_ratio, bbox, raw_features):
    conn = get_conn()
    cur = conn.execute(
        """INSERT INTO inspection_records
           (timestamp, image_name, defect_class, confidence, severity,
            defect_area_ratio, bbox, raw_features)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), image_name,
         defect_class, confidence, severity, defect_area_ratio,
         json.dumps(bbox), json.dumps(raw_features)),
    )
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return rid


def query_history(limit=50):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM inspection_records ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def stats_summary():
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) AS n FROM inspection_records").fetchone()["n"]
    rows = conn.execute(
        "SELECT defect_class, COUNT(*) AS n FROM inspection_records GROUP BY defect_class"
    ).fetchall()
    severity_rows = conn.execute(
        "SELECT severity, COUNT(*) AS n FROM inspection_records GROUP BY severity"
    ).fetchall()
    conn.close()
    ok = sum(r["n"] for r in severity_rows if r["severity"] == "良品")
    return {
        "total": total,
        "pass_rate": round(ok / total * 100, 2) if total else 0.0,
        "by_class": {r["defect_class"]: r["n"] for r in rows},
        "by_severity": {r["severity"]: r["n"] for r in severity_rows},
    }
