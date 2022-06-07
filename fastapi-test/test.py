import sqlite3
from fastapi import FastAPI

CREATE_TABLE = """CREATE TABLE IF NOT EXISTS test (word TEXT, number REAL);"""
INSERT_ROW = "INSERT INTO test (word, number) VALUES (?, ?);"
GET_ALL_DATA = "SELECT * FROM test;"
app = FastAPI()

def connect():
    return sqlite3.connect("test.db", isolation_level=None, check_same_thread=False)

@app.get("/create")
def create_tables():
    #context manager, when we create database, it gets saved to the ^^ file
    connection.execute(CREATE_TABLE)

connection = connect()

@app.get("/dump")
def dump():
    return connection.execute(GET_ALL_DATA)

@app.get("/fill")
def fill():
    connection.execute(INSERT_ROW, ('hello', 123))

@app.get("/")
async def root():
    return {"message": "Hello World"}

create_tables()
