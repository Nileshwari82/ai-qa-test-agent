"""Demo requirements and optional offline sample report."""

from __future__ import annotations

DEMO_REQUIREMENTS: dict[str, str] = {
    "Login": (
        "User should be able to log in using a valid email address and password. "
        "The system should show an error for invalid credentials and lock the account "
        "after 5 failed attempts."
    ),
    "Password Reset": (
        "User should be able to reset password using their registered email. "
        "A reset link should be sent to the email and expire after 24 hours."
    ),
    "User Registration": (
        "New users should be able to register with email, password, and full name. "
        "Password must meet security policy and email must be unique."
    ),
    "E-commerce Checkout": (
        "Customer should be able to checkout with cart items, shipping address, "
        "and payment method. Order confirmation should be displayed after successful payment."
    ),
    "Search": (
        "User should be able to search products by keyword. "
        "Results should be relevant and support pagination."
    ),
}
