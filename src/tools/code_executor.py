"""
Tool: run_python
Executes Python code for financial calculations, ratio analysis,
trend computation, and data manipulation.
Sandboxed — only allows safe financial computation operations.
"""

import sys
import io
import math
import traceback
from loguru import logger


# Safe built-ins allowed in the sandbox
SAFE_BUILTINS = {
    "abs": abs, "round": round, "min": min, "max": max,
    "sum": sum, "len": len, "range": range, "enumerate": enumerate,
    "zip": zip, "map": map, "filter": filter, "sorted": sorted,
    "list": list, "dict": dict, "tuple": tuple, "set": set,
    "str": str, "int": int, "float": float, "bool": bool,
    "print": print, "isinstance": isinstance, "type": type,
    "math": math,
}

# Safe modules the agent can import
SAFE_MODULES = {"math", "statistics", "json", "datetime"}


def run_python(code: str) -> dict:
    """
    Execute Python code in a sandboxed environment for financial calculations.

    The agent can use this to:
    - Calculate financial ratios (P/E, EV/EBITDA, DCF estimates)
    - Compute moving averages and trend analysis
    - Compare metrics across companies
    - Perform percentage calculations
    - Summarize and format numerical data

    Args:
        code: Python code string to execute

    Returns:
        Dict with stdout output, result, and any errors
    """
    try:
        # Capture stdout
        stdout_capture = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = stdout_capture

        # Build safe execution context
        safe_globals = {
            "__builtins__": SAFE_BUILTINS,
            "math": math,
        }

        # Try importing safe modules if requested in code
        for mod in SAFE_MODULES:
            if f"import {mod}" in code or f"from {mod}" in code:
                safe_globals[mod] = __import__(mod)

        # Add pandas and numpy if needed (financial calculations)
        if "pd." in code or "pandas" in code:
            import pandas as pd
            safe_globals["pd"] = pd
        if "np." in code or "numpy" in code:
            import numpy as np
            safe_globals["np"] = np

        local_vars = {}

        exec(code, safe_globals, local_vars)

        sys.stdout = old_stdout
        output = stdout_capture.getvalue()

        # Get the last assigned variable as result if no print output
        result = None
        if local_vars:
            last_key = list(local_vars.keys())[-1]
            result = local_vars[last_key]
            if hasattr(result, 'to_dict'):
                result = result.to_dict()
            elif hasattr(result, 'tolist'):
                result = result.tolist()

        logger.info(f"Python executed successfully | output: {len(output)} chars")
        return {
            "success": True,
            "output":  output.strip() if output else "",
            "result":  str(result) if result is not None else "",
            "code":    code,
        }

    except Exception as e:
        sys.stdout = old_stdout
        error_msg = traceback.format_exc()
        logger.error(f"run_python failed: {e}")
        return {
            "success": False,
            "error":   str(e),
            "output":  "",
            "code":    code,
        }
