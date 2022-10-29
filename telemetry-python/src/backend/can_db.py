from typing import Any

import sqlite3
import pkg_resources, os

fields = ("timestamp TEXT", 
          "[15VS] REAL", "[19VS] REAL", "[33VS] REAL", 
          "MPPCOV REAL", "MPTC REAL", "MPCT REAL")

# names of all the fields
field_names = tuple(field.split(" ")[0].replace("[", "").replace("]", "") for field in fields)

# question mark placeholder for SQL query, e.g. (?, ?, ?, ?)
qmarks = tuple("?" for _ in fields)

# create the table
CREATE_CAN_TABLE = f"CREATE TABLE IF NOT EXISTS can_test_db ({', '.join(fields)});"

# insert an entire row
INSERT_ROW = f"INSERT INTO can_test_db VALUES ({', '.join(qmarks)});"

GET_ALL_DATA = "SELECT * FROM can_test_db;"
GET_ALL_DATA_REV = "SELECT * FROM can_test_db ORDER BY id DESC;"
SORT_BY = "SELECT * FROM can_test_db ORDER BY {field};"
SORT_BY_REV = "SELECT * FROM can_test_db ORDER BY {field} DESC;"

REMOVE_CONTACT = "DELETE FROM can_test_db WHERE id = ?;"

def connect():
    return sqlite3.connect(pkg_resources.resource_filename(
                               __name__,
                               os.path.join(os.pardir, 'resources', 'cantest_data.db')
                           ), 
                           isolation_level=None, 
                           check_same_thread=False)

def create_tables(connection: sqlite3.Connection):
    with connection:
        connection.execute(CREATE_CAN_TABLE)

def add_row(connection: sqlite3.Connection, json_row: dict[str, Any]):
    with connection:
        connection.execute(INSERT_ROW, tuple(json_row[field] for field in field_names))

def get_all_data(connection: sqlite3.Connection):
    with connection:
        return connection.execute(GET_ALL_DATA).fetchall()

def sort_by_field(connection: sqlite3.Connection, field: str):
    with connection:
        return connection.execute(SORT_BY.format(field=field)).fetchall()

def remove_row(connection: sqlite3.Connection, id_: int):
    with connection:
        connection.execute(REMOVE_CONTACT, (id_,)) # make sure second param is a tuple
