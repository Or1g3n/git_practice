import sys
import time
import random

def main():
    script_name = sys.argv[0]
    # Countdown from 20 to 0
    for i in range(10, -1, -1):
        # print(f"Countdown: {i} from {script_name}")
        print(f"Countdown: {i} from {script_name}", end='\r')
        time.sleep(1)
    print()  # Move to next line after countdown

    # 30% chance to fail
    if random.random() < 0.3:
        print("Error: Simulated failure occurred.")
        print("Failure detail: Something went wrong.")
        x = 1/0  # Intentional error to simulate failure
    else:
        print("Processing completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
