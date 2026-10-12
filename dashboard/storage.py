from pathlib import Path
import sqlite3
from datetime import datetime, timezone
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "experiments.sqlite3"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def connect():
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with connect() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            name TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            host TEXT NOT NULL,
            port INTEGER NOT NULL,
            packet_count INTEGER NOT NULL,
            interval_ms INTEGER NOT NULL,
            timeout_ms INTEGER NOT NULL,
            payload_size INTEGER NOT NULL,
            sent INTEGER NOT NULL,
            received INTEGER NOT NULL,
            loss_pct REAL NOT NULL,
            min_ms REAL,
            avg_ms REAL,
            max_ms REAL,
            p95_ms REAL,
            jitter_ms REAL,
            notes TEXT
        )
        """)
        con.execute("""
        CREATE TABLE IF NOT EXISTS packets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            sequence INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            sent_at TEXT,
            rtt_ms REAL,
            success INTEGER NOT NULL,
            error TEXT,
            FOREIGN KEY(run_id) REFERENCES runs(id)
        )
        """)

def save_run(config, packet_rows, metrics):
    started = datetime.now(timezone.utc).isoformat()
    with connect() as con:
        cur = con.execute("""
            INSERT INTO runs (
                started_at,name,endpoint,host,port,packet_count,interval_ms,
                timeout_ms,payload_size,sent,received,loss_pct,min_ms,avg_ms,
                max_ms,p95_ms,jitter_ms,notes
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            started, config["name"], config["endpoint"], config["host"],
            config["port"], config["count"], config["interval_ms"],
            config["timeout_ms"], config["payload_size"], metrics["sent"],
            metrics["received"], metrics["loss_pct"], metrics["min_ms"],
            metrics["avg_ms"], metrics["max_ms"], metrics["p95_ms"],
            metrics["jitter_ms"], config["notes"]
        ))
        run_id = cur.lastrowid
        for p in packet_rows:
            con.execute("""
                INSERT INTO packets (
                    run_id,sequence,timestamp,sent_at,rtt_ms,success,error
                ) VALUES (?,?,?,?,?,?,?)
            """, (
                run_id, p["sequence"], p["timestamp"], p["sent_at"],
                p["rtt_ms"], int(p["success"]), p["error"]
            ))
    return run_id

def get_runs():
    with connect() as con:
        return pd.read_sql_query("SELECT * FROM runs ORDER BY id DESC", con)

def get_packets(run_id):
    with connect() as con:
        return pd.read_sql_query(
            "SELECT * FROM packets WHERE run_id=? ORDER BY sequence",
            con, params=(int(run_id),)
        )

def export_run_csv(run_id):
    packets = get_packets(run_id)
    return packets.to_csv(index=False).encode("utf-8")

init_db()
