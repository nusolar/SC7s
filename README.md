# SC7s Python Telemetry System

This folder contains programs (written primarily in python) responsible
for gathering, parsing, storing, sending, and receiving CAN data
from various components in the solar car.

## Directory Structure

```
telemetry-python
├── example-data
├── scripts
└── src
    ├── can
    ├── resources
    └── xbee-tests
```

The `scripts` directory contains executable python scripts. 
* `virtual_system.py` simulates the entire telemetry pipeline without
  need for a real CAN bus connection or XBees. This is useful for testing
  without connecting to a live CAN bus.
* `onboard.py` parses CAN data from the bus, sends the data as JSON from one
  XBee radio device to another. This program is intended to run onboard the car
  and send parsed data via XBees to the basestation.
* `virtual_onboard.py` functions similar to `onboard.py`, except
  that, like `virtual_system.py`, the CAN traffic is simulated.
* `remote.py`, running on the basestation, receives
  parsed data from `onboard.py` and stores it in a
  database.
* `dbc_builder.py` provides a way to conveniently create dbc
  files for devices on the CAN bus based off 'abstract' dbc files
  for these devices. It can, for example, create a dbc file for three
  MPPT devices (say, one at base adress `0x600`, another at `0x610`,
  and the third at `0x620`) by using `abstract_mppt.dbc` (in `src/resources`).

The `example-data` folder contains CAN data, both raw
and parsed, collected off MPPTs, motor controllers, etc.

The `src` contains classes and functions leveraged by the
programs in `scripts`. 
* `sql.py` contains helper functions for database interactions.
* `util.py` contains various minor utilites.
* Modules in the `can` directory contains logic for managing, simulating, and
  serializing aggregrate CAN data.
* `resources` houses all non-source-code files which are relevant to the system,
  including dbc files, SQLite databases, etc.

## Setup

First, download the repository and go this directory

```bash
$ git clone https://github.com/nusolar/SC7s
$ cd telemetry-python
```

It is highly recommended to use a virtual environment like `venv`
or `direnv`. Refer to [this article](https://python.land/virtual-environments/virtualenv)
to familiarize yourself with virtual environments.

Once in a virtual environment, you can run

```bash
$ pip install -e .
```
to install all the required packages.
