# this is the code that only interacts with the database
from typing import ItemsView

from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from src.can.row import Row, CanValue

# Add queries separately so it's easier to change later on

def create_tables(session: Session, tablename: str, columns: ItemsView[str, CanValue]):
    """
    Creates a SQL table using SQLAlchemy with a provided name and values

    Parameters
    ----------
    Session : session
        a SQLAlchemy session object
    tablename : str
        name of the created SQL table
    columns : ItemsView[str, CanValue]
        a view where keys are column names (str) and the values are CanValue objects.

    Returns
    ----------
    None
    """
    signal_columns = ",\n".join(f"{k} {'REAL' if v.is_averaged else 'INT'}" for k, v in columns)

    CREATE_CAN_TABLE = f"CREATE TABLE IF NOT EXISTS {tablename} (timestamp INT, {signal_columns})"

    session.execute(text(CREATE_CAN_TABLE))
                
def add_row(session: Session, r: Row):
    """
    Adds a row to a database table using SQLAlchemy

    Parameters
    ----------
    Session : session
        a SQLAlchemy session object
    r : Row
        a Row object containing name, timestamp, and signals

    Returns
    ----------
    None
    """
    vals = ["NULL" if v.value is None else str(v.value) for v in r.signals.values()]
    
    insert_row = f"INSERT INTO {r.name} VALUES ({r.timestamp}, {(','.join(vals))})"

    session.execute(text(insert_row))
    session.commit()

