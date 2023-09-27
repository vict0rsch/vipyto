import subprocess


def run_command(command):
    """
    Run a shell command and return the output.
    """
    return subprocess.check_output(command.split(" ")).decode("utf-8").strip()
