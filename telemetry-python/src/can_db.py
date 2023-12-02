# for can_recv_app.py
# this is the code that only interacts with the database

from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

# Add queries separately so it's easier to change later on

def create_tables(session: Session, tablename: str, columns):
    #context manager, when we create database, it gets saved to the ^^ file

    #create a string of question marks depending on # of column values
    columns = "(timestamp REAL,\n" \
              + ",\n".join(f"{k} {'REAL' if v.is_averaged else 'INT'}" for k, v in columns) \
              + ")"

    CREATE_CAN_TABLE = f"""CREATE TABLE IF NOT EXISTS {tablename}\n {columns}"""

    session.execute(text(CREATE_CAN_TABLE))
                
def add_row(session: Session, r_timestamp: float | None, r_values, r_name: str):
    placeholder = "%s" if isinstance(dbEngine, PostgresEngine) else "?"
    qmarks = f"({placeholder}, " + ", ".join(placeholder for _ in r_values) + ")"
    vals = [r_timestamp] + [v.value for v in r_values]
    insert_row = f"INSERT INTO {r_name} VALUES\n" + qmarks



