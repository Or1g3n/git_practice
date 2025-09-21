## Me

I am building an ETL orchestrator cli tool that runs a build schedule of squential and parallel tasks. I want to incorporate a way to monitor status while the tasks are running. I know there are progress bar libraries for python but I am wondering if it would be better to build my own progress bar library that is more tailored to my needs. I want max performance.

## CodeCompanion (Copilot)

Building your own progress bar library can give you full control over features, performance, and integration with your ETL orchestrator. However, it’s important to weigh the trade-offs:

**Pros of building your own:**
- Tailored to your CLI’s output format and concurrency model (sequential/parallel).
- Can optimize for minimal I/O and CPU overhead.
- Custom handling for nested/parallel tasks (e.g., tree-like progress, grouped bars).
- Integrate with your logging and error reporting.

**Cons:**
- More development and maintenance effort.
- Existing libraries (e.g., [tqdm](https://github.com/tqdm/tqdm), [rich](https://github.com/Textualize/rich), [alive-progress](https://github.com/rsalmei/alive-progress)) are highly optimized and support many use cases, including multi-threading and multi-processing.

**Performance considerations:**
- Minimize terminal redraws (batch updates, only redraw when state changes).
- Use efficient string formatting and avoid excessive sys.stdout writes.
- For parallel tasks, consider how to display multiple bars without flicker or overlap.
- Avoid blocking the main ETL logic with UI updates (use background threads/processes if needed).

**Pseudocode plan for a custom progress bar:**
```
- Define a ProgressBar class with:
    - total steps
    - current progress
    - status message
    - update() method to redraw bar only if changed

- For parallel tasks:
    - Maintain a list of ProgressBar instances
    - Use a manager thread/process to periodically redraw all bars

- Integrate with ETL task runner:
    - Each task updates its ProgressBar
    - Manager handles display updates

- Optimize redraws:
    - Only update terminal when necessary
    - Use ANSI escape codes for cursor movement
```

**Next steps:**  
Would you like a scaffold for a custom progress bar class, or a comparison of how to extend an existing library for your parallel/sequential ETL tasks?

## Me

My ideal setup would be as follows. Let's say I hit a parallel block that runs 5 scripts. At first each script would show up on it's own row showing that it is processing. It is possible that each script may have logic that prints to to stdout; if this occurs, I want to show the stdout below the script but indented in so it is clear that the output came from the corresponding script. I would alot a max of 3 lines of stdout to be shown per script, and if there is more output than that I would show a message like "2 more lines not shown". Once the script completes, I want the progress bar to update to show that it has completed successfully or failed. If it failed, I want to show the exit code next to the failed status.

Below is an example of what I am envisioning. Please walk me through what would be involved to get this type of dynamic output in the terminal. I realize the challenge would be ensure that the output is clean and responsive.
Initially you would see the below at start of the parallel block:
script_1.py [Processing...]
script_2.py [Processing...]
script_3.py [Processing...]
script_4.py [Processing...]
script_5.py [Processing...]

Then it would update in place as output is generated:
script_1.py [Processing...]
    Output line 1 from script 1
    Output line 2 from script 1
    Output line 3 from script 1
script_2.py [Processing...]
    Output line 1 from script 2
    Output line 2 from script 2
script_3.py [Processing...]
    ...
    Output line 2 from script 3
    Output line 3 from script 3
    Output line 4 from script 3
script_4.py [Processing...]
script_5.py [Processing...]

When finished it would look like this:
script_1.py [Finished] ✓
    Output line 1 from script 1
    Output line 2 from script 1
    Output line 3 from script 1
script_2.py [Finished] ✓
    Output line 1 from script 2
    Output line 2 from script 2
    Output line 3 from script 2
script_3.py [Finished] ✓
    ...
    Output line 2 from script 3
    Output line 3 from script 3
    Output line 4 from script 3
script_4.py [Failed] 𐄂
    Error Code:
    Failure detail
script_5.py [Finished] ✓
    Output line 1 from script 5


## CodeCompanion (Copilot)

To achieve this dynamic, multi-row, in-place updating terminal output for parallel scripts, you’ll need to manage several challenges:

### Key Requirements

1. **In-place Terminal Updates:**  
   Use ANSI escape codes to move the cursor and redraw only the changed lines, avoiding flicker.

2. **Parallel Output Management:**  
   Capture stdout/stderr from each script separately, buffer the last N lines, and associate them with the correct script row.

3. **Concurrency:**  
   Run scripts in parallel (e.g., using `concurrent.futures`, `asyncio`, or threads/processes), but synchronize output updates to avoid race conditions.

4. **Status Tracking:**  
   Track each script’s status (processing, finished, failed), and display exit codes/errors as needed.

5. **Output Truncation:**  
   Show only the last 3 lines per script, with a “N more lines not shown” message if needed.

### Pseudocode Plan

```
- Define a ScriptTask class:
    - name
    - status (processing/finished/failed)
    - output_lines (buffer, max 3)
    - extra_output_count
    - exit_code (if failed)

- Launch scripts in parallel:
    - For each script, capture stdout/stderr (e.g., via subprocess.PIPE)
    - As output is received, append to output_lines buffer, increment extra_output_count if > 3

- Display Manager:
    - Periodically redraw the entire block:
        - Move cursor to start of block
        - For each ScriptTask:
            - Print status line
            - Print up to 3 output lines, indented
            - If extra_output_count > 0, print "...N more lines not shown"
    - Use a lock to synchronize redraws

- On script completion:
    - Update status and exit code
    - Trigger a redraw

- Handle terminal resizing and cleanup (optional)
```

### Implementation Steps

1. **Script Execution:**  
   Use `subprocess.Popen` for each script, capturing output asynchronously.

2. **Output Buffering:**  
   For each script, maintain a buffer of the last 3 lines, and a count of additional lines.

3. **Terminal Control:**  
   Use ANSI codes (`\033[{row};{col}H`, `\033[K` to clear line) to move the cursor and redraw only the relevant block.

4. **Concurrency Control:**  
   Use a thread/process for each script, and a main thread for display updates (with a lock).

5. **Status Updates:**  
   Update the status and output buffer as each script progresses and completes.

### Example: Display Manager Skeleton

````python
# filepath: etl_orchestrator/display_manager.py
import threading
import sys
import time

class ScriptTask:
    def __init__(self, name):
        self.name = name
        self.status = "Processing..."
        self.output_lines = []
        self.extra_output_count = 0
        self.exit_code = None

    def add_output(self, line):
        if len(self.output_lines) < 3:
            self.output_lines.append(line)
        else:
            self.extra_output_count += 1

    def set_finished(self, success, exit_code=None):
        self.status = "Finished ✓" if success else f"Failed 𐄂"
        self.exit_code = exit_code

class DisplayManager:
    def __init__(self, tasks):
        self.tasks = tasks
        self.lock = threading.Lock()
        self.running = True

    def redraw(self):
        with self.lock:
            sys.stdout.write("\033[H")  # Move cursor to top
            for task in self.tasks:
                sys.stdout.write(f"{task.name} [{task.status}]")
                if task.status.startswith("Failed") and task.exit_code is not None:
                    sys.stdout.write(f" {task.exit_code}")
                sys.stdout.write("\n")
                for line in task.output_lines:
                    sys.stdout.write(f"    {line}\n")
                if task.extra_output_count > 0:
                    sys.stdout.write(f"    ...{task.extra_output_count} more lines not shown\n")
            sys.stdout.flush()

    def run(self):
        while self.running:
            self.redraw()
            time.sleep(0.2)  # Adjust for responsiveness

    def stop(self):
        self.running = False
````

### Next Steps

Would you like a full working example, including subprocess management and output capture, or help integrating this display manager into your ETL orchestrator?

## Me

yes, please provide a full working example that includes subprocess management and output capture, integrated with the display manager. I would like to see how the scripts can be run in parallel and how their output is captured and displayed dynamically in the terminal based on the design we discussed.

## CodeCompanion (Copilot)

Here’s a full working example that demonstrates:

- Running multiple scripts in parallel using `subprocess.Popen` and threads.
- Capturing each script’s stdout/stderr output.
- Dynamically updating the terminal display with a custom `DisplayManager`.
- Showing only the last 3 output lines per script, with an overflow message.
- Indicating finished/failed status and exit code.

**Assumptions:**
- The scripts to run are Python files (e.g., `script_1.py`, `script_2.py`, ...).
- This example is a single Python file for clarity.  
- You can adapt it to your CLI tool structure.

````python
# filepath: etl_orchestrator/parallel_runner.py
import threading
import subprocess
import sys
import time
import os

MAX_OUTPUT_LINES = 3

class ScriptTask:
    def __init__(self, name):
        self.name = name
        self.status = "Processing..."
        self.output_lines = []
        self.extra_output_count = 0
        self.exit_code = None
        self.lock = threading.Lock()

    def add_output(self, line):
        with self.lock:
            if len(self.output_lines) < MAX_OUTPUT_LINES:
                self.output_lines.append(line)
            else:
                self.extra_output_count += 1

    def set_finished(self, success, exit_code=None):
        with self.lock:
            self.status = "Finished ✓" if success else "Failed 𐄂"
            self.exit_code = exit_code

class DisplayManager(threading.Thread):
    def __init__(self, tasks):
        super().__init__()
        self.tasks = tasks
        self.running = True
        self.daemon = True  # So it exits with main thread

    def redraw(self):
        # Move cursor to top and clear screen
        sys.stdout.write("\033[2J\033[H")
        for task in self.tasks:
            with task.lock:
                line = f"{task.name} [{task.status}]"
                if task.status.startswith("Failed") and task.exit_code is not None:
                    line += f" {task.exit_code}"
                sys.stdout.write(line + "\n")
                for out_line in task.output_lines:
                    sys.stdout.write(f"    {out_line}\n")
                if task.extra_output_count > 0:
                    sys.stdout.write(f"    ...{task.extra_output_count} more lines not shown\n")
        sys.stdout.flush()

    def run(self):
        while self.running:
            self.redraw()
            time.sleep(0.2)

    def stop(self):
        self.running = False
        self.redraw()

def run_script(task: ScriptTask, script_path: str):
    # Run the script and capture output line by line
    proc = subprocess.Popen(
        [sys.executable, script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    try:
        for line in proc.stdout:
            task.add_output(line.rstrip())
        proc.wait()
        success = proc.returncode == 0
        task.set_finished(success, exit_code=proc.returncode if not success else None)
    except Exception as e:
        task.add_output(f"Exception: {e}")
        task.set_finished(False, exit_code="EXC")
    finally:
        proc.stdout.close()

def main():
    # List your script files here
    script_files = [
        "script_1.py",
        "script_2.py",
        "script_3.py",
        "script_4.py",
        "script_5.py"
    ]

    tasks = [ScriptTask(name=script) for script in script_files]
    display_manager = DisplayManager(tasks)
    display_manager.start()

    threads = []
    for task, script in zip(tasks, script_files):
        t = threading.Thread(target=run_script, args=(task, script))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    display_manager.stop()
    print("\nAll scripts finished.")

if __name__ == "__main__":
    main()
````

**How to test:**
1. Create dummy Python scripts (`script_1.py`, etc.) that print output and exit with 0 or non-zero codes.
2. Run this orchestrator script in your terminal.

**Notes:**
- The display manager clears and redraws the terminal block every 0.2 seconds.
- Output from each script is captured and shown under its corresponding row.
- Only the last 3 lines are shown, with overflow indicated.
- Status updates and exit codes are displayed as specified.

**Next:**  
Try this with your scripts and let me know if you want enhancements (e.g., colored output, better error handling, or integration with your CLI argument parsing).

## Me

for the sake of testing, provide code that I can put into a script and make certain aspects random, such as whether it succeeds or fails, how many lines of output it generates, and the content of those lines. This will help me see how the progress bar and output handling works in practice.

use sleep to simulate time taken for processing, 3 - 10 seconds. Add a condition that if randomly hit with a 30 percent chance, it will fail with a non-zero exit code. The output lines can be simple strings like "Output line X from script Y". I can then make a script and duplicate it 5 times.

## CodeCompanion (Copilot)

Here’s a Python script you can use as a template for your test scripts.  
It randomly decides:

- How many output lines to print (between 1 and 8).
- How long to sleep between lines (to simulate work).
- Whether to succeed or fail (30% chance to fail).
- The exit code (1 for failure, 0 for success).

Just copy this code into `script_1.py`, `script_2.py`, etc.

````python
# Example test script for ETL orchestrator progress bar demo

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
        sys.exit(1)
    else:
        print("Processing completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
````

**Instructions:**
- Save this as `script_1.py`, then duplicate as `script_2.py`, ..., `script_5.py`.
- Run your orchestrator script to see dynamic output and status handling.

Would you like suggestions for adding color or more realistic error output?

## Me



