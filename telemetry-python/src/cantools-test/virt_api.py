import sqlite3
from fastapi import FastAPI

GET_ALL_DATA = "SELECT * FROM virtdata;"
DROP_TABLE   = "DROP TABLE virtdata;"
app = FastAPI()

def connect():
    return sqlite3.connect("virt.db", isolation_level=None, check_same_thread=False)

@app.get("/dump")
def dump():
    return connection.execute(GET_ALL_DATA).fetchall()

@app.get("/latest")
def latest():
    return connection.execute(GET_ALL_DATA)

@app.get("/drop")
def drop():
    return connection.execute(DROP_TABLE)

@app.get("/")
async def root():
    return {"message": "Hello World"}

connection = connect()
