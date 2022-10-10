import can_db #from same folder

#open database connection
connection = can_db.connect()
can_db.create_tables(connection)
#initial list of contacts
contacts = can_db.get_all_data(connection)

#easy way to print out all the contacts
def see_all_contacts():
    print("\n~List~")
    global contacts
    for name in contacts:
        print(f"{name[0]}. {name[1]} {name[2]}  {name[5]} {name[4]} in {name[3]}. {name[6]}\n")
        #ex. 3. Jake from Deering

see_all_contacts()