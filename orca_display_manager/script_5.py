import sys
import time
import random

def main():
    script_name = sys.argv[0]
    num_lines = random.randint(1, 8)
    total_sleep = random.uniform(3, 10)
    sleep_per_line = total_sleep / num_lines

    for i in range(1, num_lines + 1):
        print(f"Output line {i} from {script_name}")
        time.sleep(sleep_per_line)

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
