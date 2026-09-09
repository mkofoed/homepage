"""Tests for the public showcase API.

These endpoints are unauthenticated and publicly reachable, so the tests cover
the contract (status codes, response shape) and the guards that keep a hostile
query string from turning into unbounded work.

The anonymous throttle is backed by the cache, and the locmem cache is shared
across tests in a process. Each case clears it so one test's request count
cannot throttle the next one.
"""

from unittest.mock import patch

from django.conf import settings
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework.throttling import SimpleRateThrottle

from showcase.services.algorithms import (
    calculate_operation,
    check_palindrome,
    generate_fibonacci,
)
from showcase.services.content import PROGRAMMING_QUOTES, get_random_quote


class ShowcaseAPITestCase(TestCase):
    """Shared setup: a DRF client and a clean throttle bucket."""

    def setUp(self) -> None:
        cache.clear()
        self.client = APIClient()

    def tearDown(self) -> None:
        cache.clear()


class EchoEndpointTests(ShowcaseAPITestCase):
    def test_echo_returns_message_length_and_reversal(self) -> None:
        response = self.client.get(reverse("api_echo"), {"message": "Hello"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"message": "Hello", "length": 5, "reversed": "olleH"},
        )

    def test_echo_falls_back_to_a_default_message(self) -> None:
        response = self.client.get(reverse("api_echo"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Hello, World!")

    def test_echo_does_not_interpret_html_in_the_message(self) -> None:
        """The response is JSON, so markup must survive as inert text."""
        response = self.client.get(reverse("api_echo"), {"message": "<script>x</script>"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "<script>x</script>")


class CalculateEndpointTests(ShowcaseAPITestCase):
    def test_each_supported_operation_returns_its_result(self) -> None:
        cases = [
            ("add", 10, 5, 15),
            ("subtract", 10, 5, 5),
            ("multiply", 10, 5, 50),
            ("divide", 10, 5, 2),
        ]

        for operation, a, b, expected in cases:
            with self.subTest(operation=operation):
                response = self.client.post(
                    reverse("api_calculate"),
                    {"a": a, "b": b, "operation": operation},
                    format="json",
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["result"], expected)

    def test_division_by_zero_is_rejected_rather_than_raising(self) -> None:
        response = self.client.post(
            reverse("api_calculate"),
            {"a": 1, "b": 0, "operation": "divide"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Division by zero")

    def test_unknown_operation_returns_bad_request(self) -> None:
        response = self.client.post(
            reverse("api_calculate"),
            {"a": 1, "b": 2, "operation": "exponentiate"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Unknown operation", response.json()["error"])

    def test_non_numeric_operands_return_bad_request(self) -> None:
        response = self.client.post(
            reverse("api_calculate"),
            {"a": "not-a-number", "b": 2, "operation": "add"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_get_is_not_allowed(self) -> None:
        response = self.client.get(reverse("api_calculate"))

        self.assertEqual(response.status_code, 405)


class FibonacciEndpointTests(ShowcaseAPITestCase):
    def test_sequence_and_sum_are_returned(self) -> None:
        response = self.client.get(reverse("api_fibonacci"), {"n": 7})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["sequence"], [0, 1, 1, 2, 3, 5, 8])
        self.assertEqual(payload["sum"], 20)

    def test_request_for_a_huge_sequence_is_capped_at_fifty(self) -> None:
        """The cap is the only thing standing between this endpoint and a cheap DoS."""
        response = self.client.get(reverse("api_fibonacci"), {"n": 10000})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["n"], 50)
        self.assertEqual(len(payload["sequence"]), 50)

    def test_non_positive_n_returns_bad_request(self) -> None:
        response = self.client.get(reverse("api_fibonacci"), {"n": 0})

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_non_integer_n_returns_bad_request(self) -> None:
        response = self.client.get(reverse("api_fibonacci"), {"n": "abc"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())


class PalindromeEndpointTests(ShowcaseAPITestCase):
    def test_punctuation_and_case_are_ignored(self) -> None:
        response = self.client.get(reverse("api_palindrome"), {"text": "A man, a plan, a canal: Panama"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["is_palindrome"])
        self.assertEqual(payload["cleaned"], "amanaplanacanalpanama")

    def test_non_palindrome_is_reported_as_such(self) -> None:
        response = self.client.get(reverse("api_palindrome"), {"text": "hello"})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["is_palindrome"])

    def test_empty_text_is_not_a_palindrome(self) -> None:
        response = self.client.get(reverse("api_palindrome"), {"text": ""})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["is_palindrome"])


class RandomQuoteEndpointTests(ShowcaseAPITestCase):
    def test_quote_has_the_documented_shape(self) -> None:
        response = self.client.get(reverse("api_random_quote"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(set(payload), {"quote", "author"})
        self.assertIn(payload, PROGRAMMING_QUOTES)


class ThrottlingTests(ShowcaseAPITestCase):
    """These endpoints are public and uncached, so the throttle is the only brake."""

    def test_settings_keep_anonymous_throttling_enabled(self) -> None:
        self.assertIn(
            "rest_framework.throttling.AnonRateThrottle",
            settings.REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"],
        )
        self.assertIn("anon", settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"])

    def test_exceeding_the_anonymous_rate_returns_429(self) -> None:
        """DRF binds THROTTLE_RATES onto the throttle class at import time, so
        `override_settings` never reaches it. Patch the resolved table instead."""
        with patch.dict(SimpleRateThrottle.THROTTLE_RATES, {"anon": "2/hour"}):
            self.assertEqual(self.client.get(reverse("api_echo")).status_code, 200)
            self.assertEqual(self.client.get(reverse("api_echo")).status_code, 200)
            self.assertEqual(self.client.get(reverse("api_echo")).status_code, 429)


class SchemaTests(ShowcaseAPITestCase):
    def test_showcase_endpoints_appear_in_the_generated_schema(self) -> None:
        """extend_schema metadata must keep producing a valid schema."""
        response = self.client.get(reverse("schema"))

        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        for path in (
            "/api/showcase/echo/",
            "/api/showcase/calculate/",
            "/api/showcase/fibonacci/",
            "/api/showcase/palindrome/",
            "/api/showcase/random-quote/",
        ):
            self.assertIn(path, body)


class AlgorithmServiceTests(SimpleTestCase):
    """The service layer is where the logic lives, so it is tested directly too."""

    def test_calculate_operation_returns_none_for_division_by_zero(self) -> None:
        self.assertIsNone(calculate_operation(1, 0, "divide"))

    def test_calculate_operation_rejects_an_unknown_operation(self) -> None:
        with self.assertRaises(ValueError):
            calculate_operation(1, 2, "modulo")

    def test_generate_fibonacci_truncates_to_the_requested_length(self) -> None:
        self.assertEqual(generate_fibonacci(1), [0])
        self.assertEqual(generate_fibonacci(2), [0, 1])
        self.assertEqual(generate_fibonacci(5), [0, 1, 1, 2, 3])

    def test_generate_fibonacci_rejects_non_positive_input(self) -> None:
        for value in (0, -1):
            with self.subTest(n=value), self.assertRaises(ValueError):
                generate_fibonacci(value)

    def test_check_palindrome_strips_non_alphanumeric_characters(self) -> None:
        self.assertEqual(check_palindrome("Ra-ce car!"), ("racecar", True))

    def test_check_palindrome_treats_blank_input_as_not_a_palindrome(self) -> None:
        self.assertEqual(check_palindrome("   "), ("", False))


class QuoteServiceTests(SimpleTestCase):
    def test_every_quote_has_text_and_an_author(self) -> None:
        for entry in PROGRAMMING_QUOTES:
            with self.subTest(quote=entry["quote"][:30]):
                self.assertTrue(entry["quote"].strip())
                self.assertTrue(entry["author"].strip())

    def test_get_random_quote_returns_a_known_quote(self) -> None:
        self.assertIn(get_random_quote(), PROGRAMMING_QUOTES)
