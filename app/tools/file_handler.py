import sys
from app.tools.utils import tool

@tool
def read_file(file_path: str) -> str:
    """ Read and return the content of a file.
    :param file_path: The path to the file to read.
    """
    try:
        with open(file_path) as f:
            content = f.read()
            return content
    except Exception as e:
        error_msg = f"Error reading file: {e}"
        print(error_msg, file=sys.stderr)
        return error_msg


@tool
def Write(file_path: str, content: str) -> str:
    """Write content to a file.
    :param file_path: The path of the file to write to.
    :param content: The content to write to the file.
    """
    try:
        with open(file_path, "w") as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        error_msg = f"Error writing to file: {e}"
        print(error_msg, file=sys.stderr)
        return error_msg
