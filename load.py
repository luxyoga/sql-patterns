#!/usr/bin/env python3
"""Build the practice database. Usage: python load.py [duckdb|sqlite]"""
import sys, pathlib

engine = (sys.argv[1] if len(sys.argv) > 1 else "duckdb").lower()
schema = pathlib.Path("data/01_schema.sql").read_text()
seed = pathlib.Path("data/02_seed.sql").read_text()

if engine == "duckdb":
    import duckdb
    con = duckdb.connect("practice.duckdb")
    con.execute(schema); con.execute(seed)
    n = con.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    print(f"practice.duckdb ready: {n} orders, 40 customers")
    print("open it with:  duckdb practice.duckdb")
elif engine == "sqlite":
    import sqlite3
    con = sqlite3.connect("practice.db")
    con.executescript(schema); con.executescript(seed); con.commit()
    n = con.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    print(f"practice.db ready: {n} orders, 40 customers")
    print("open it with:  sqlite3 practice.db")
else:
    sys.exit("usage: python load.py [duckdb|sqlite]")
