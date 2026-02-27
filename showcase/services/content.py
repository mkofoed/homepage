import random

PROGRAMMING_QUOTES: list[dict[str, str]] = [
    {"quote": "Code is like humor. When you have to explain it, it's bad.", "author": "Cory House"},
    {"quote": "First, solve the problem. Then, write the code.", "author": "John Johnson"},
    {"quote": "Experience is the name everyone gives to their mistakes.", "author": "Oscar Wilde"},
    {"quote": "In order to be irreplaceable, one must always be different.", "author": "Coco Chanel"},
    {"quote": "Java is to JavaScript what car is to Carpet.", "author": "Chris Heilmann"},
    {"quote": "Knowledge is power.", "author": "Francis Bacon"},
    {
        "quote": "Sometimes it pays to stay in bed on Monday, rather than spending the rest of the week debugging Monday's code.",
        "author": "Dan Salomon",
    },
    {
        "quote": "Perfection is achieved not when there is nothing more to add, but rather when there is nothing more to take away.",
        "author": "Antoine de Saint-Exupery",
    },
    {"quote": "Code never lies, comments sometimes do.", "author": "Ron Jeffries"},
    {"quote": "Simplicity is the soul of efficiency.", "author": "Austin Freeman"},
]


def get_random_quote() -> dict[str, str]:
    """Return a random inspirational programming quote."""
    return random.choice(PROGRAMMING_QUOTES)
