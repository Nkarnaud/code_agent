import subprocess
from app.tools.utils import tool


@tool
def Bash(command: str) -> str:
    """Execute a shell command
    :param command: The command to execute
    """
    result = subprocess.run(command.split(), capture_output=True, text=True)
    if result.stderr:
        return result.stderr
    return result.stdout
