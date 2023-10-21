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
* `real_bus.py` is a simple CAN parser that reads off a CAN
  bus and prints the parsed data to the terminal. This is
  used for testing.
* `virtual_bus.py` is similar to `real_bus.py`, except the CAN
  Bus is simulated and data is mocked. This is useful for testing
  without connecting to a live CAN bus.
* `sender.py` parses CAN data from the bus, like `real_bus.py`,
  but sends the data as JSON from one XBee radio device
  to another. This program is intended to run onboard the
  car and send parsed data via XBees to the basestation.
* `virtual_sender.py` functions similar to `sender.py`, except
  that, like `virtual_bus.py`, the CAN traffic is simulated.
* `receiver.py`, running on the basestation, receives
  parsed data from `sender.py` and stores them in a
  database.
* `solar_car_display.py` monitors CAN data and presents
  is an onboard dispay to the driver.
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
