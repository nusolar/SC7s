import cantools.database

db = cantools.database.load_file('MPPT.dbc')
print([[sig.is_float for sig in msg.signals] for msg in db.messages])
