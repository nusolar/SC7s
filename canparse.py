import csv
import struct, binascii

class CANParser:
    def __init__(self, table_file: str):
        """Initialize a lookup dictionary from a CSV file."""
        self.table = {}
        with open(table_file) as table_file:
            csv_reader = csv.DictReader(table_file)
            for row in csv_reader:
                if int(row['CAN_ID'], 16) in self.table:
                    self.table[int(row['CAN_ID'], 16)] += [row]
                else:
                    self.table[int(row['CAN_ID'], 16)] = [row]
                del row['CAN_ID']

    def parse(self, message: str) -> dict:
        """
        Take a CAN message in hexadecimal
        and return a dictionary of values.
        """

        result_list = []
        try:
            rows = self.table[int(message[0:3], 16)]
        except KeyError:
            return result_list

        for row in rows:
            results = {}
            results['Tag'] = row['Tag']
            hex_offset = int(row['Offset'], 10) * 2
            hex_length = int(row['Length'], 10) * 2
            results['data'] = struct.unpack('<' + row['Type'],
                binascii.unhexlify(message[3 + hex_offset:3 + hex_offset + hex_length]))[0]
            result_list += [results]
        return result_list

