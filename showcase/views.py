"""
Showcase API views demonstrating various API patterns.
"""

import logging

from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

logger = logging.getLogger(__name__)


# Programming quotes moved to services


@extend_schema(
    summary="Echo a message",
    description="Returns the message you send back to you. Useful for testing API connectivity.",
    parameters=[
        OpenApiParameter(
            name="message",
            description="The message to echo back",
            required=False,
            type=str,
            examples=[
                OpenApiExample("Hello", value="Hello, World!"),
            ],
        ),
    ],
    responses={200: dict},
)
@api_view(["GET"])
def echo(request: Request) -> Response:
    """Echo back the provided message."""
    message: str = request.query_params.get("message", "Hello, World!")
    return Response(
        {
            "message": message,
            "length": len(message),
            "reversed": message[::-1],
        }
    )


@extend_schema(
    summary="Simple calculator",
    description="Perform basic arithmetic operations: add, subtract, multiply, divide.",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "example": 10},
                "b": {"type": "number", "example": 5},
                "operation": {"type": "string", "enum": ["add", "subtract", "multiply", "divide"], "example": "add"},
            },
            "required": ["a", "b", "operation"],
        }
    },
    responses={200: dict},
)
@api_view(["POST"])
def calculate(request: Request) -> Response:
    """Perform a calculation on two numbers."""
    try:
        a: float = float(request.data.get("a", 0))
        b: float = float(request.data.get("b", 0))
        operation: str = request.data.get("operation", "add")

        from .services.algorithms import calculate_operation

        try:
            result = calculate_operation(a, b, operation)
            if result is None:
                return Response({"error": "Division by zero"}, status=400)

            return Response(
                {
                    "a": a,
                    "b": b,
                    "operation": operation,
                    "result": result,
                }
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

    except (ValueError, TypeError) as e:
        return Response({"error": str(e)}, status=400)


@extend_schema(
    summary="Random programming quote",
    description="Get a random inspirational programming quote.",
    responses={200: dict},
)
@api_view(["GET"])
def random_quote(request: Request) -> Response:
    """Return a random programming quote."""
    from .services.content import get_random_quote

    return Response(get_random_quote())


@extend_schema(
    summary="Generate Fibonacci sequence",
    description="Generate the first N numbers in the Fibonacci sequence.",
    parameters=[
        OpenApiParameter(
            name="n",
            description="Number of Fibonacci numbers to generate (max 50)",
            required=False,
            type=int,
            examples=[
                OpenApiExample("10 numbers", value=10),
            ],
        ),
    ],
    responses={200: dict},
)
@api_view(["GET"])
def fibonacci(request: Request) -> Response:
    """Generate Fibonacci sequence."""
    from .services.algorithms import generate_fibonacci

    try:
        n: int = min(int(request.query_params.get("n", 10)), 50)
        sequence = generate_fibonacci(n)

        return Response(
            {
                "n": n,
                "sequence": sequence,
                "sum": sum(sequence),
            }
        )
    except ValueError as e:
        return Response({"error": str(e)}, status=400)


@extend_schema(
    summary="Palindrome checker",
    description="Check if a given text is a palindrome (reads the same forwards and backwards).",
    parameters=[
        OpenApiParameter(
            name="text",
            description="Text to check",
            required=True,
            type=str,
            examples=[
                OpenApiExample("Racecar", value="racecar"),
                OpenApiExample("Hello", value="hello"),
            ],
        ),
    ],
    responses={200: dict},
)
@api_view(["GET"])
def palindrome(request: Request) -> Response:
    """Check if text is a palindrome."""
    from .services.algorithms import check_palindrome

    text: str = request.query_params.get("text", "")
    clean, is_palindrome = check_palindrome(text)

    return Response(
        {
            "text": text,
            "cleaned": clean,
            "is_palindrome": is_palindrome,
        }
    )
