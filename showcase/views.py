"""
Showcase API views demonstrating various API patterns.
"""
import logging
import random

from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

logger = logging.getLogger(__name__)


PROGRAMMING_QUOTES: list[dict[str, str]] = [
    {"quote": "Code is like humor. When you have to explain it, it's bad.", "author": "Cory House"},
    {"quote": "First, solve the problem. Then, write the code.", "author": "John Johnson"},
    {"quote": "Experience is the name everyone gives to their mistakes.", "author": "Oscar Wilde"},
    {"quote": "In order to be irreplaceable, one must always be different.", "author": "Coco Chanel"},
    {"quote": "Java is to JavaScript what car is to Carpet.", "author": "Chris Heilmann"},
    {"quote": "Knowledge is power.", "author": "Francis Bacon"},
    {"quote": "Sometimes it pays to stay in bed on Monday, rather than spending the rest of the week debugging Monday's code.", "author": "Dan Salomon"},
    {"quote": "Perfection is achieved not when there is nothing more to add, but rather when there is nothing more to take away.", "author": "Antoine de Saint-Exupery"},
    {"quote": "Code never lies, comments sometimes do.", "author": "Ron Jeffries"},
    {"quote": "Simplicity is the soul of efficiency.", "author": "Austin Freeman"},
]


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
@api_view(['GET'])
def echo(request: Request) -> Response:
    """Echo back the provided message."""
    message: str = request.query_params.get('message', 'Hello, World!')
    return Response({
        'message': message,
        'length': len(message),
        'reversed': message[::-1],
    })


@extend_schema(
    summary="Simple calculator",
    description="Perform basic arithmetic operations: add, subtract, multiply, divide.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'a': {'type': 'number', 'example': 10},
                'b': {'type': 'number', 'example': 5},
                'operation': {'type': 'string', 'enum': ['add', 'subtract', 'multiply', 'divide'], 'example': 'add'},
            },
            'required': ['a', 'b', 'operation'],
        }
    },
    responses={200: dict},
)
@api_view(['POST'])
def calculate(request: Request) -> Response:
    """Perform a calculation on two numbers."""
    try:
        a: float = float(request.data.get('a', 0))
        b: float = float(request.data.get('b', 0))
        operation: str = request.data.get('operation', 'add')
        
        operations: dict[str, callable] = {
            'add': lambda x, y: x + y,
            'subtract': lambda x, y: x - y,
            'multiply': lambda x, y: x * y,
            'divide': lambda x, y: x / y if y != 0 else None,
        }
        
        if operation not in operations:
            logger.warning("Unknown operation requested: %s", operation)
            return Response({'error': f'Unknown operation: {operation}'}, status=400)
        
        result = operations[operation](a, b)
        
        if result is None:
            logger.warning("Division by zero attempted: %s / %s", a, b)
            return Response({'error': 'Division by zero'}, status=400)
        
        logger.info("Calculate: %s %s %s = %s", a, operation, b, result)
        return Response({
            'a': a,
            'b': b,
            'operation': operation,
            'result': result,
        })
    except (ValueError, TypeError) as e:
        return Response({'error': str(e)}, status=400)


@extend_schema(
    summary="Random programming quote",
    description="Get a random inspirational programming quote.",
    responses={200: dict},
)
@api_view(['GET'])
def random_quote(request: Request) -> Response:
    """Return a random programming quote."""
    quote: dict[str, str] = random.choice(PROGRAMMING_QUOTES)
    return Response(quote)


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
@api_view(['GET'])
def fibonacci(request: Request) -> Response:
    """Generate Fibonacci sequence."""
    try:
        n: int = min(int(request.query_params.get('n', 10)), 50)
        
        if n <= 0:
            return Response({'error': 'n must be positive'}, status=400)
        
        fib: list[int] = [0, 1]
        while len(fib) < n:
            fib.append(fib[-1] + fib[-2])
        
        return Response({
            'n': n,
            'sequence': fib[:n],
            'sum': sum(fib[:n]),
        })
    except ValueError:
        return Response({'error': 'Invalid number'}, status=400)


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
@api_view(['GET'])
def palindrome(request: Request) -> Response:
    """Check if text is a palindrome."""
    text: str = request.query_params.get('text', '')
    clean: str = ''.join(c.lower() for c in text if c.isalnum())
    is_palindrome: bool = clean == clean[::-1]
    
    return Response({
        'text': text,
        'cleaned': clean,
        'is_palindrome': is_palindrome,
    })
