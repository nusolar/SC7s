import sqlite3
from src.can.row import Row
from src import ROOT_DIR
from pathlib import Path

db_conn = sqlite3.connect((Path(ROOT_DIR).joinpath("resources", "mppt.dbc")))

curr = db_conn.cursor()

curr.execute("SELECT * FROM MPPT_0x600")

MPPT_data = curr.fetchall()

for d in MPPT_data:
    d
    