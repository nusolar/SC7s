# for can_recv_app.py
# this is the code that only interacts with the database

import sqlite3
import psycopg2
import pkg_resources, os
from pathlib import Path
from src import ROOT_DIR

# Add queries separately so it's easier to change later on

GET_ALL_DATA = "SELECT * FROM can_test_db;"

def connect(dbEngine, filename="TEST"):
    # open data file. if not there, create one
    # os and pathlib are used to create the db file in the same location every
    # time.

    # sqlite db_file version
    if dbEngine == 1:
        db_file = Path(ROOT_DIR).joinpath('resources', f"{filename}.db")
        return sqlite3.connect(db_file, isolation_level=None, check_same_thread=False)
    # db_file = pkg_resources.resource_filename(
    #     __name__,
    #     os.path.join(os.pardir, 'resources', f"{filename}.db"))
    elif dbEngine == 2:
        return psycopg2.connect(
            host = "localhost",
            database = "testing",
            # user = "jasonhu27",
            # password = "Esketit123"
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
        if dbEngine == 1:
            connection.execute(CREATE_CAN_TABLE)
        elif dbEngine == 2:
            cursor = connection.cursor()
            cursor.execute(CREATE_CAN_TABLE)
            connection.commit()


def add_row(connection, r_timestamp, r_values, r_name, dbEngine):
    qmarks = f"(%s, " + ", ".join("%s" for _ in r_values) + ")"
    vals = [r_timestamp] + [v.value for v in r_values]
    insert_row = f"INSERT INTO {r_name} VALUES\n" + qmarks

    with connection:
        if dbEngine == 1:
            connection.execute(insert_row, vals)
        elif dbEngine == 2:
            cursor = connection.cursor()
            cursor.execute(insert_row, vals) # 2nd param has to be tuple
            connection.commit()


def get_all_data(connection, dbEngine):
    with connection:
        if dbEngine == 1:
            return connection.execute(GET_ALL_DATA).fetchall()
        elif dbEngine == 2:
            cursor = connection.cursor()
            return cursor.execute(GET_ALL_DATA).fetchall()
