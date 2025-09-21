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
        self.failed = False

    def add_output(self, line):
        with self.lock:
            if not self.failed:
                if len(self.output_lines) < MAX_OUTPUT_LINES:
                    self.output_lines.append(line)
                else:
                    # Remove oldest, keep only last 3
                    self.output_lines.pop(0)
                    self.output_lines.append(line)
                    self.extra_output_count += 1
            else:
                # If failed, keep all lines
                self.output_lines.append(line)

    def set_finished(self, success, exit_code=None):
        with self.lock:
            self.status = "Finished ✓" if success else "Failed 𐄂"
            self.exit_code = exit_code
            if not success:
                self.failed = True  # Allow all lines to be shown

class DisplayManager(threading.Thread):
    def __init__(self, tasks):
        super().__init__()
        self.tasks = tasks
        self.running = True
        self.daemon = True  # So it exits with main thread
        self.block_lines = 0

    def redraw(self):
        # Calculate number of lines to print
        lines = 0
        for task in self.tasks:
            lines += 1  # status line
            if not task.failed and task.extra_output_count > 0:
                lines += 1
            lines_to_show = task.output_lines if task.failed else task.output_lines[-MAX_OUTPUT_LINES:]
            lines += len(lines_to_show)
        # Move cursor up by block_lines (if not first draw)
        if self.block_lines:
            sys.stdout.write(f"\033[{self.block_lines}A")
        output = []
        for task in self.tasks:
            with task.lock:
                line = f"{task.name} [{task.status}]"
                if task.status.startswith("Failed") and task.exit_code is not None:
                    line += f" {task.exit_code}"
                output.append(line)
                if not task.failed and task.extra_output_count > 0:
                    output.append(f"    ...{task.extra_output_count} more lines not shown")
                lines_to_show = task.output_lines if task.failed else task.output_lines[-MAX_OUTPUT_LINES:]
                for out_line in lines_to_show:
                    output.append(f"    {out_line}")
        # Print block, clearing each line
        for line in output:
            sys.stdout.write(line + "\033[K\n")
        sys.stdout.flush()
        self.block_lines = lines

    def run(self):
        while self.running:
            self.redraw()
            time.sleep(0.2)

    def stop(self):
        self.running = False
        self.redraw()

# def run_script(task: ScriptTask, script_path: str):
#     # Run the script and capture output line by line
#     proc = subprocess.Popen(
#         [sys.executable, "-u", script_path],  # <-- add "-u"
#         stdout=subprocess.PIPE,
#         stderr=subprocess.STDOUT,
#         text=True,
#         bufsize=1
#     )
#     try:
#         for line in proc.stdout:
#             task.add_output(line.rstrip())
#         proc.wait()
#         success = proc.returncode == 0
#         task.set_finished(success, exit_code=proc.returncode if not success else None)
#     except Exception as e:
#         task.add_output(f"Exception: {e}")
#         task.set_finished(False, exit_code="EXC")
#     finally:
#         proc.stdout.close()

def run_script(task: ScriptTask, script_path: str):
    # Run the script and capture output character-by-character to handle \r
    proc = subprocess.Popen(
        [sys.executable, "-u", script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    try:
        buffer = ""
        while True:
            char = proc.stdout.read(1)
            if not char:
                break
            if char == '\r':
                buffer = ""
            elif char == '\n':
                task.add_output(buffer)
                buffer = ""
            else:
                buffer += char
        if buffer:
            task.add_output(buffer)
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
