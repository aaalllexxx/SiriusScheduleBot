import json
import os
import signal
import sys
import time
from platform import system
from threading import Thread


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def launch(filename, pyversion):
    if system() == "Windows":
        os.popen(f"python {filename}")
    else:
        os.popen(f"{pyversion} {filename}")


def clear_output():
    with open(".checker_stdout", "w") as file:
        file.close()


def get_output():
    if os.path.exists(".checker_stdout"):
        with open(".checker_stdout") as file:
            content = file.read()
        if content:
            for i in content.split("\n"):
                print(i)
        clear_output()


class Checker:
    def __init__(self, pid):
        stack = traceback.extract_stack()
        filename = stack[0].filename.split(os.sep)[-1]
        with open("checker.json", "w") as file:
            file.write(json.dumps({f"{filename}_process_id": pid}))

    @staticmethod
    def view_file(filename, pyversion="python3"):
        thread = Thread(target=launch, args=(filename, pyversion))
        thread.run()
        print(f"{Colors.BOLD + Colors.FAIL}Start watching...{Colors.ENDC}")
        with open(filename, "r", encoding="utf8") as file:
            start = file.read()

        while True:
            get_output()
            with open("checker.json", "r") as file:
                data = json.loads(file.read())
            pid = data.get(f"{filename.split(os.sep)[-1]}_process_id")
            time.sleep(0.2)
            with open(filename, "r", encoding="utf8") as file:
                current = file.read()

            if start != current:
                print(f"{Colors.BOLD + Colors.FAIL}Restarting...{Colors.ENDC}")
                if pid:
                    start = current
                    print(f"Killing process {pid}...")
                    if system() == "Windows":
                        os.popen(f"taskkill /F /PID {pid}")
                    else:
                        os.kill(pid, signal.SIGKILL)
                print("Launching script...")
                try:
                    thread = Thread(target=launch, args=(filename, pyversion))
                    thread.run()
                except Exception as e:
                    print(e)
                    print("Restarting...")
                    thread = Thread(target=launch, args=(filename, pyversion))
                    thread.run()


if __name__ == "__main__":
    Checker.view_file(sys.argv[1])

if __name__ != "__main__":
    import traceback


    def print(*args):
        stack = traceback.extract_stack()
        filename = stack[0].filename
        args = list(args)
        for i in range(len(args)):
            args[i] = str(args[i])
        with open(".checker_stdout", "r") as file:
            content = file.read()
            content = content + '\n' if content else ""
        with open(".checker_stdout", "w+") as file:
            file.write(
                f"{Colors.OKBLUE}# log {filename.split(os.sep)[-1]} {Colors.ENDC} --[ {Colors.OKGREEN}{content}{', '.join(args)}{Colors.ENDC}")
        sys.stdout.write(f"{', '.join(args)}")
