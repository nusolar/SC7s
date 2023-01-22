import json
from backend import can_db
import pkg_resources, os

connection = can_db.connect()
can_db.create_tables(connection)

def add_data_from_file(input_filename):
    with open(input_filename) as input_file:
        for line in input_file:
            json_row = json.loads(line)
            can_db.add_row(connection, json_row)


def main():
    # open database connection
    # initial list of contacts
    filename = pkg_resources.resource_filename(
        __name__,
        os.path.join(os.pardir, 'example-data', 'mppt_parsed.txt')
    )
    add_data_from_file(filename)

main()