#for can_recv_app.py
#this is the code that only interacts with the database

import sqlite3
import pkg_resources, os

g = ["KEY", "Timestamp" , "15VS", "19VS", "33VS", "MPPCOV", "MPTC", "MPCT"]

#add queries separately so it's easier to change later on
CREATE_CAN_TABLE = """CREATE TABLE IF NOT EXISTS can_test_db 
(Timestamp TEXT, [15VS] REAL, [19VS] REAL, [33VS] REAL, MPPCOV REAL, MPTC REAL, MPCT REAL);"""
#id INTEGER PRIMARY KEY, 
INSERT_ROW = "INSERT INTO can_test_db (Timestamp, 15VS, 19VS, 33VS, MPPCOV, MPTC, MPCT) VALUES (?, ?, ?, ?, ?, ?, ?);" #include inputs for ? when used
INSERT_VAL = "INSERT INTO can_test_db VALUES (?, ?, ?, ?, ?, ?, ?)"

GET_ALL_DATA = "SELECT * FROM can_test_db;"
GET_ALL_DATA_REV = "SELECT * FROM can_test_db ORDER BY id DESC;"
SORT_BY = "SELECT * FROM can_test_db ORDER BY {field};"
SORT_BY_REV = "SELECT * FROM can_test_db ORDER BY {field} DESC;"

REMOVE_CONTACT = "DELETE FROM can_test_db WHERE id = ?;"

def connect():
    #open data file. if not there, create one
    # os and pathlib are used to create the db file in the same location every
    # time.
    return sqlite3.connect(pkg_resources.resource_filename(
                               __name__,
                               os.path.join(os.pardir, os.pardir, 'resources', 'cantest_data.db')
                           ), 
                           isolation_level=None, 
                           check_same_thread=False)

def create_tables(connection):
    #context manager, when we create database, it gets saved to the ^^ file
    with connection:
        connection.execute(CREATE_CAN_TABLE)

def add_row(connection, json_row):
    # Timestamp = row[0]
    # VS15 = row[1]
    # VS19 = row[2]
    # VS33 = row[3]
    # MPPCOV = row[4]
    # MPTC = row[5]
    # MPCT = row[6]
    # with connection:
    #     connection.execute(INSERT_ROW, (Timestamp, VS15, VS19, VS33, MPPCOV, MPTC, MPCT)) #second param has to be tuple
    with connection:
        connection.execute(INSERT_VAL, (json_row["timestamp"], json_row["15VS"], json_row["19VS"], json_row["33VS"], json_row["MPPCOV"], json_row["MPTC"], json_row["MPCT"])) #second param has to be tuple

def get_all_data(connection):
    with connection:
        return connection.execute(GET_ALL_DATA).fetchall()

def sort_by_field(connection, field):
    with connection:
        return connection.execute(SORT_BY.format(field=field)).fetchall()
        #fetch all gives us a list of rows

def reverse_sort_by_field(connection, field):
    if ("Timestamp" in field):
        field = "Timestamp"
    elif ("15VS" in field):
        field = "15VS"
    elif ("19VS" in field):
        field = "19VS"
    elif ("33VS" in field):
        field = "33VS"
    else:
        field = "id"

    with connection:
        return connection.execute(SORT_BY_REV.format(field=field)).fetchall()
        #fetch all gives us a list of rows

def remove_row(connection, id):
    with connection:
        connection.execute(REMOVE_CONTACT, (id,)) #second param has to be tuple
