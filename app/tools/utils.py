import inspect
from typing import Optional, Any, Callable, get_type_hints


PYTHON_TO_JSON_TYPES = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}

TOOLS: dict[str, dict[str, Any]] = {}


def build_tool_definition(func: Callable) -> dict[str, Any]:
    hints = get_type_hints(func)
    hints.pop("return", None)
    sig = inspect.signature(func)
    properties = {}

    for param_name, param_type in hints.items():
        json_type = PYTHON_TO_JSON_TYPES.get(param_type, "string")
        param_doc = ""
        if func.__doc__:
            for line in func.__doc__.splitlines():
                if f":param {param_name}:" in line:
                    param_doc = line.split(f":param {param_name}")[1].strip()
                    break
        properties[param_name] = {"type": json_type, "description": param_doc}

    required = [
        name for name, param, in sig.parameters.items()
        if param.default is inspect.Parameter.empty
    ]

    description = ""
    if func.__doc__:
        description = func.__doc__.strip().splitlines()[0].strip()
    
    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


def tool(func: Callable) -> Callable:
    TOOLS[func.__name__] = {"definition": build_tool_definition(func), "handler": func}
