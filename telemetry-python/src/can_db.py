# for can_recv_app.py
# this is the code that only interacts with the database

import sqlite3
import psycopg2
from dataclasses import dataclass
from pathlib import Path

# Classes for the different databases
@dataclass
class SQLiteEngine:
    path: Path

@dataclass
class PostgresEngine:
    host: str
    database: str

# Add queries separately so it's easier to change later on

GET_ALL_DATA = "SELECT * FROM can_test_db;"

def connect(dbEngine: SQLiteEngine | PostgresEngine):
    match dbEngine:
        case SQLiteEngine(path):
            return sqlite3.connect(path, isolation_level=None, check_same_thread=False)
        case PostgresEngine(host, database):
            return psycopg2.connect(
                host = host,
                database = database,
            )

def create_tables(connection, tablename, columns, dbEngine):
    #context manager, when we create database, it gets saved to the ^^ file

    #create a string of question marks depending on # of column values
    columns = "(timestamp REAL,\n" \
              + ",\n".join(f"{k} {'REAL' if v.is_averaged else 'INT'}" for k, v in columns) \
              + ")"

    CREATE_CAN_TABLE = f"""CREATE TABLE IF NOT EXISTS {tablename}\n {columns}"""

    # not global anymore - the tablename and such 
    with connection:
        match dbEngine:
            case SQLiteEngine(_):
                connection.execute(CREATE_CAN_TABLE)
            case PostgresEngine(_):
                cursor = connection.cursor()
                cursor.execute(CREATE_CAN_TABLE)
                connection.commit()
                
def add_row(connection, r_timestamp, r_values, r_name, dbEngine):
    placeholder = "%s" if isinstance(dbEngine, PostgresEngine) else "?"
    qmarks = f"({placeholder}, " + ", ".join(placeholder for _ in r_values) + ")"
    
    vals = [r_timestamp] + [v.value for v in r_values]
    insert_row = f"INSERT INTO {r_name} VALUES\n" + qmarks

    with connection:
        match dbEngine:
            case SQLiteEngine(_):
                connection.execute(insert_row, vals)
            case PostgresEngine(_):
                cursor = connection.cursor()
                cursor.execute(insert_row, vals) # 2nd param has to be tuple
                connection.commit()

def get_all_data(connection, dbEngine):
    with connection:
        match dbEngine:
            case SQLiteEngine(_):
                return connection.execute(GET_ALL_DATA).fetchall()
            case PostgresEngine(_):
                cursor = connection.cursor()
                return cursor.execute(GET_ALL_DATA).fetchall()
