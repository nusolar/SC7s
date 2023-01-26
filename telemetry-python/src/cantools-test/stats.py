import random

UINT8_MAX = 0xFF

# (mean, stddev) for different signals
# Very loosely based on real data
MPIV_STATS   = (9.75, 0.1)
MPIC_STATS   = (0.0005, 0.0001)
MPOV_STATS   = (10.3, 0.1)
MPOC_STATS   = (6e-5, 1e-5)
MPMST_STATS  = (23.8, 0.1)
MPCT_STATS   = (30.4, 0.1)
MP12V_STATS  = (12.0, 0.05)
MP3V_STATS   = (3.0, 0.05)
MPMOV_STATS  = (109.1, 0.0)
MPMIC_STATS  = (7.0, 0.0)
MPPCOV_STATS = (10.5, 0.2)
MPPCT_STATS  = (23.65, 0.01)

test_counters: dict[str, int] = {}

def init_counter(node_name: str):
    """
    Initialize test counter for node
    """
    global test_counters
    test_counters[node_name] = random.randint(0, UINT8_MAX)

def inc_counter(node_name: str) -> int:
    """
    Increment test counter with modular arithmetic.
    """
    global test_counters

    test_counters[node_name] = (test_counters[node_name] + 1) % (UINT8_MAX + 1)

    return test_counters[node_name]

def mock_value(node_name: str, signal_name: str) -> float | int:
    """
    Make a mock value for a signal.
    """
    if "MPPT" in node_name:
        match signal_name:
            case "Input_voltage":
                return random.normalvariate(*MPIV_STATS)
            case "Input_current":
                return random.normalvariate(*MPIC_STATS)
            case "Output_voltage":
                return random.normalvariate(*MPOV_STATS)
            case "Output_current":
                return random.normalvariate(*MPOC_STATS)
            case "Mosfet_temperature":
                return random.normalvariate(*MPMST_STATS)
            case "Controller_temperature":
                return random.normalvariate(*MPCT_STATS)
            case "Twelve_V":
                return random.normalvariate(*MP12V_STATS)
            case "Three_V":
                return random.normalvariate(*MP3V_STATS)
            case "Max_output_voltage":
                return random.normalvariate(*MPMOV_STATS)
            case "Max_input_current":
                return random.normalvariate(*MPMIC_STATS)
            case "CAN_RX_error_counter":
                return 0 # RX error counter is 0, for simplicity
            case "CAN_TX_error_counter":
                return 0 # TX error counter is 0, for simplicity
            case "CAN_TX_overflow_counter":
                return 0 # TX overflow counter is 0, for simplicity
            case "Mode":
                return 1 # Mode = 1 for "on." 0 is for "standby."
            case "Test_counter":
                if node_name not in test_counters:
                    init_counter(node_name)
                return inc_counter(node_name) # Increment test counter every time
            case "Power_connector_output_voltage":
                return random.normalvariate(*MPPCOV_STATS)
            case "Power_connector_temperature":
                return random.normalvariate(*MPPCT_STATS)
            case "Sweep_input_voltage":
                return 0 # TODO: maybe collect real data for sweep measurments
            case "Sweep_input_current":
                return 0 # TODO: maybe collect real data for sweep measurments
            case _:
                return 0 # No error / limit flags are set, for simplicity
    else:
        raise Exception(f"Unknown node: {node_name}")
