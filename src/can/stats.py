import random

UINT8_MAX = 0xFF

# (mean, stddev) for different signals
# Very loosely based on real data
#
# TODO: Get better data for more devices to base the virtual data
# off of.
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

MCBV_STATS   = (12.93, 0.1)
MCVD_STATS   = (0.4, 0.2)
MCVQ_STATS   = (0.9, 0.2)
MC15V_STATS  = (15.0, 0.2)
MC3V3_STATS  = (3.3, 0.05)
MC1V9_STATS  = (1.9, 0.05)
MCHST_STATS  = (17.7, 0.2)
MCMT_STATS   = (24.5, 0.2)
MCDBT_STATS  = (20.9, 0.2)

test_counters: dict[str, int] = {}

def init_counter(node_name: str):
    """
    Initialize test counter for node

    Parameters
    ----------
    node_name : str
        the name of the node being tested

    Returns
    ----------
    None
    """
    global test_counters
    test_counters[node_name] = random.randint(0, UINT8_MAX)

def inc_counter(node_name: str) -> int:
    """
    Increment test counter with modular arithmetic.

    Parameters
    ----------
    node_name : str
        the name of the node being incremented

    Returns
    ----------
    None
    """
    global test_counters

    test_counters[node_name] = (test_counters[node_name] + 1) % (UINT8_MAX + 1)

    return test_counters[node_name]

# TODO: Add "playback mode", where `mock_value` pulls from real data recorded
# previously.
def mock_value(node_name: str, signal_name: str) -> float | int:
    """
    Generates a mock value for a signal.

    Parameters
    ----------
    node_name : str
        the name of the node for which the mock value is being created for
    signal_name : str
        the name of the signal for which the mock value is being created for

    Returns
    ----------
    int, float : 
        the generated mock value
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
    elif "MOTOR_CONTROLLER" in node_name:
        match signal_name:
            case "SerialNumber":
                return 123456
            case "TritiumID":
                return 943206484
            case "RxErrorCount":
                return 0
            case "TxErrorCount":
                return 0
            case "ActiveMotor":
                return 0
            case "ErrorFlags":
                return 16
            case "LimitFlags":
                return 0
            case "BusCurrent":
                return 0.0
            case "BusVoltage":
                return random.normalvariate(*MCBV_STATS)
            case "VehicleVelocity":
                return 0.0
            case "MotorVelocity":
                return 0.0
            case "PhaseCurrentB":
                return 0.0
            case "PhaseCurrentC":
                return 0.0
            case "Vd":
                return random.normalvariate(*MCVD_STATS)
            case "Vq":
                return random.normalvariate(*MCVQ_STATS)
            case "Id":
                return 0.0
            case "Iq":
                return 0.0
            case "BEMFq":
                return 0.0
            case "BEMFd":
                return 0.0
            case "Supply15V":
                return random.normalvariate(*MC15V_STATS)
            case "Supply3V3":
                return random.normalvariate(*MC3V3_STATS)
            case "Supply1V9":
                return random.normalvariate(*MC1V9_STATS)
            case "HeatsinkTemp":
                return random.normalvariate(*MCHST_STATS)
            case "MotorTemp":
                return random.normalvariate(*MCMT_STATS)
            case "DspBoardTemp":
                return random.normalvariate(*MCDBT_STATS)
            case "DCBusAh":
                return 0.0
            case "Odometer":
                return 0.0
            case "SlipSpeed":
                return 0.0
            case s if "Reserved" in s:
                return 0.0
            case _:
                raise Exception(f"Unknown motor contoller signal name: {signal_name}")
    elif "DriverControl" in node_name:
        match signal_name:
            case "TritiumID":
                return 943206484
            case "SerialNumber":
                return 123456
            case "SetpointMotorVelocity":
                return 0.0
            case "SetpointMotorCurrent":
                return 0.0
            case s if "Reserved" in s:
                return 0
            case "SetpointBusCurrent":
                return 0.0
            case "Unused_1":
                return 0
            case "Unused_2":
                return 0
            case "ModeReverse":
                return 0
            case "ModeNetural":
                return 0
            case "ModeRegen":
                return 0
            case "ModeDrive":
                return 0
            case "IgnitionAccesories":
                return 0
            case "IgnitionRun":
                return 0
            case "IgnitionStart":
                return 0
            case "Brake":
                return 0
            case "ChargePort":
                return 0
            case "Flags":
                return 0
            case "State":
                return 0
            case _:
                raise Exception(f"Unknown driver controls signal name: {signal_name}")
    else:
        raise Exception(f"Unknown node: {node_name}")
