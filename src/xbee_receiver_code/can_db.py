#for can_recv_app.py
#this is the code that only interacts with the database

import sqlite3

g = ["KEY", "Timestamp" , "15VS", "19VS", "33VS"]

#add queries separately so it's easier to change later on
CREATE_CAN_TABLE = """CREATE TABLE IF NOT EXISTS can_test_db 
(id INTEGER PRIMARY KEY, Timestamp TEXT, 15VS REAL, 19VS REAL, 33VS REAL);"""

INSERT_ROW = "INSERT INTO contacts (Timestamp, 15VS, 19VS, 33VS) VALUES (?, ?, ?, ?);" #include inputs for ? when used

GET_ALL_DATA = "SELECT * FROM can_test_db;"
GET_ALL_DATA_REV = "SELECT * FROM cant_test_db ORDER BY id DESC;"
SORT_BY = "SELECT * FROM can_test_db ORDER BY {field};"
SORT_BY_REV = "SELECT * FROM can_test_db ORDER BY {field} DESC;"

REMOVE_CONTACT = "DELETE FROM can_test_db WHERE id = ?;"

def connect():
    #open data file. if not there, create one
    return sqlite3.connect("cantest_data.db", isolation_level=None)

def create_tables(connection):
    #context manager, when we create database, it gets saved to the ^^ file
    with connection:
        connection.execute(CREATE_CAN_TABLE)

def add_row(connection, row):
    Timestamp = row[0]
    VS15 = row[1]
    VS19 = row[2]
    VS33 = row[33]
    with connection:
        connection.execute(INSERT_ROW, (Timestamp, VS15, VS19, VS33)) #second param has to be tuple

def get_all_data(connection):
    with connection:
        return connection.execute(GET_ALL_DATA_REV).fetchall()

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