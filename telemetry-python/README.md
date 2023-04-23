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
    ├── backend
    ├── can
    ├── resources
    └── xbee-tests
```

The `scripts` directory contains executable python scripts. 
* `no_gui.py` is a simple CAN parser that reads off a serial
  port and prints the parsed data to the terminal. This is
  used for testing.
* `sender.py` parses CAN data off a serial port, like `no_gui.py`,
  but sends the data as JSON from one XBee radio device
  to another. This program is intended to run onboard the
  car and send parsed data via XBees to the basestation.
* `can_recv_app.py`, running on the basestation, receives
  parsed data from `sender.py` and stores them in a
  database.
* `solar_car_display.py` monitors CAN data and presents
  is an onboard dispay to the driver.
* `gps_display.py` is not relevant yet.

The `example-data` folder contains CAN data, both raw
and parsed, collected off MPPTs, motor controllers, etc.

The `src` contains classes and functions leveraged by the
programs in `scripts`. 
* The `can` library contains logic for parsing CAN data 
  off a serial port. It uses `resources/can_table.csv`
  to determine descriptions and data from raw CAN frames.
* `backend` provides functions related to managing the
  database of CAN values on the basestation.
* `xbee-tests` contains some files used for testing
  XBee radio connections.

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
$ make install
```
to install all the required packages.

**DO NOT** use `pip install -r`. The `Makefile`
provides a wrapper around this to ensure that our code is also installed as
an editable package.

If you install a third-party package using `pip` during development, make sure
to add this to `requirements.txt`. Do this by running

```bash
$ make freeze > requirements.txt
```

**DO NOT** use `pip freeze`. The `Makefile` provides a wrapper around this
to ensure that our editable package is handled correctly.

**DO NOT** run `make freeze` if you are not in a virtual environment.
This will end up polluting `requirements.txt` with unneeded packages.
