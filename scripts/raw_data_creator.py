import json
import random
from datetime import datetime
import time

def generate_mppt_message(mppt_id):
    """Generate simulated MPPT CAN messages"""
    base_id = 1536 + (mppt_id * 16)  # 0x600, 0x610, or 0x620
    messages = []
    
    # Input measurements
    input_msg = {
        "id": base_id,
        "data": format(random.uniform(20, 40), '.2f').encode().hex() +  # voltage
                format(random.uniform(1, 5), '.2f').encode().hex()      # current
    }
    messages.append(input_msg)
    
    # Output measurements
    output_msg = {
        "id": base_id + 1,
        "data": format(random.uniform(12, 14), '.2f').encode().hex() +  # voltage
                format(random.uniform(0, 10), '.2f').encode().hex()     # current
    }
    messages.append(output_msg)
    
    # Temperature
    temp_msg = {
        "id": base_id + 2,
        "data": format(random.uniform(30, 50), '.2f').encode().hex() +  # MOSFET temp
                format(random.uniform(25, 40), '.2f').encode().hex()    # Controller temp
    }
    messages.append(temp_msg)
    
    return messages

def main():
    """Generate test data file for all MPPTs"""
    output_file = "testInputRaw.txt"
    
    with open(output_file, 'w') as f:
        # Generate 100 samples
        for _ in range(100):
            # Generate data for all 3 MPPTs
            for mppt_id in range(3):
                messages = generate_mppt_message(mppt_id)
                for msg in messages:
                    f.write(json.dumps(msg) + '\n')
            
if __name__ == "__main__":
    main()