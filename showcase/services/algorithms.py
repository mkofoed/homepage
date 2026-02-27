import logging
from collections.abc import Callable

logger = logging.getLogger(__name__)


def calculate_operation(a: float, b: float, operation: str) -> float | None:
    """Perform a calculation on two numbers.

    Args:
        a: First number
        b: Second number
        operation: 'add', 'subtract', 'multiply', or 'divide'

    Returns:
        The result of the operation, or None if division by zero.
        Raises ValueError if unknown operation.
    """
    operations: dict[str, Callable[[float, float], float | None]] = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y if y != 0 else None,
    }

    if operation not in operations:
        logger.warning("Unknown operation requested: %s", operation)
        raise ValueError(f"Unknown operation: {operation}")

    result = operations[operation](a, b)
    if result is None:
        logger.warning("Division by zero attempted: %s / %s", a, b)
    else:
        logger.info("Calculate: %s %s %s = %s", a, operation, b, result)

    return result


def generate_fibonacci(n: int) -> list[int]:
    """Generate the first N numbers in the Fibonacci sequence."""
    if n <= 0:
        raise ValueError("n must be positive")

    fib: list[int] = [0, 1]
    while len(fib) < n:
        fib.append(fib[-1] + fib[-2])
    return fib[:n]


def check_palindrome(text: str) -> tuple[str, bool]:
    """Check if text is a palindrome.

    Returns:
        Tuple of (cleaned_text, is_palindrome)
    """
    clean: str = "".join(c.lower() for c in text if c.isalnum())
    is_palindrome: bool = clean == clean[::-1] if clean else False
    return clean, is_palindrome
