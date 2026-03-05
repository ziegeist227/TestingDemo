# tests/test_step2_feature.py
#
# ══════════════════════════════════════════════════════════════════
#  STEP 2 — Feature / Functional Tests: the Checkout feature
#
#  We are testing the COMPLETE "Place Order" feature end-to-end:
#    add items to cart  →  checkout  →  order confirmed  →  cart cleared
#
#  KEY DIFFERENCES FROM UNIT TESTS (Step 1):
#    - NO mocking. All real modules are used: cart, inventory,
#      orders, notifications.
#    - Tests are written against REQUIREMENTS, not function signatures.
#    - Each test describes a user-visible behaviour, not an internal detail.
#    - We test the feature as a BLACK BOX: we only control inputs and
#      observe outputs — we do NOT look at internal state of orders.py.
#
#  KEY DIFFERENCES FROM INTEGRATION TESTS (Step 3):
#    - We test ONE complete feature (checkout), not the wiring between
#      specific module pairs.
#    - Tests represent realistic user scenarios (happy path, sad paths).
#    - We are not deliberately breaking internal interfaces here.
# ══════════════════════════════════════════════════════════════════
#
# Run with:
#     pytest tests/test_step2_feature.py -v

import pytest
import cart
import inventory
import notifications
import checkout


# ── Shared setup ──────────────────────────────────────────────────────────────
# Reset ALL state before every test — feature tests touch the whole system.

def setup_function():
    inventory.reset_stock()
    notifications.clear()
    cart.reset_all_carts()


# ══════════════════════════════════════════════════════════════════════════════
#  REQUIREMENT 1
#  "A customer with items in their cart can complete a checkout.
#   On success, their order is confirmed and their cart is cleared."
# ══════════════════════════════════════════════════════════════════════════════

class TestCheckoutHappyPath:

    def test_checkout_single_item_succeeds(self):
        """
        PRECONDITION : Customer has 1 item in cart, item is in stock.
        ACTION       : Customer checks out.
        POSTCONDITION: Checkout succeeds and returns an order ID.
        """
        cart.add_to_cart("alice@example.com", "laptop", 2)

        result = checkout.checkout("alice@example.com")

        assert result.success is True
        assert len(result.order_ids) == 1

    def test_checkout_clears_cart_on_success(self):
        """
        PRECONDITION : Customer has items in cart.
        ACTION       : Customer checks out successfully.
        POSTCONDITION: Cart is empty after checkout.
        """
        cart.add_to_cart("alice@example.com", "mouse", 5)

        checkout.checkout("alice@example.com")

        assert cart.get_cart("alice@example.com") == {}

    def test_checkout_multi_item_cart_succeeds(self):
        """
        PRECONDITION : Customer has 3 different items in cart, all in stock.
        ACTION       : Customer checks out.
        POSTCONDITION: Checkout succeeds and returns one order ID per item.
        """
        cart.add_to_cart("bob@example.com", "laptop", 1)
        cart.add_to_cart("bob@example.com", "mouse", 3)
        cart.add_to_cart("bob@example.com", "keyboard", 2)

        result = checkout.checkout("bob@example.com")

        assert result.success is True
        assert len(result.order_ids) == 3

    def test_checkout_reduces_stock_for_all_items(self):
        """
        PRECONDITION : Customer cart has laptop×2 and mouse×10.
        ACTION       : Customer checks out.
        POSTCONDITION: Stock reflects the deduction for both items.
        """
        cart.add_to_cart("carol@example.com", "laptop", 2)
        cart.add_to_cart("carol@example.com", "mouse", 10)

        checkout.checkout("carol@example.com")

        assert inventory.get_stock("laptop") == 8    # 10 - 2
        assert inventory.get_stock("mouse") == 40    # 50 - 10

    def test_checkout_sends_confirmation_per_item(self):
        """
        PRECONDITION : Customer cart has 2 items.
        ACTION       : Customer checks out.
        POSTCONDITION: Two separate confirmation notifications are sent,
                       one for each item, both addressed to the customer.
        """
        cart.add_to_cart("dana@example.com", "laptop", 1)
        cart.add_to_cart("dana@example.com", "keyboard", 1)

        checkout.checkout("dana@example.com")

        sent = notifications.get_sent()
        assert len(sent) == 2
        assert all(n["email"] == "dana@example.com" for n in sent)


# ══════════════════════════════════════════════════════════════════════════════
#  REQUIREMENT 2
#  "A customer cannot check out with an empty cart."
# ══════════════════════════════════════════════════════════════════════════════

class TestCheckoutEmptyCart:

    def test_checkout_with_empty_cart_fails(self):
        """
        PRECONDITION : Customer has no items in their cart.
        ACTION       : Customer attempts to check out.
        POSTCONDITION: Checkout fails with a meaningful error message.
        """
        result = checkout.checkout("ed@example.com")

        assert result.success is False
        assert "empty" in result.message.lower()

    def test_checkout_empty_cart_sends_no_notification(self):
        result = checkout.checkout("ed@example.com")

        assert result.success is False
        assert len(notifications.get_sent()) == 0


# ══════════════════════════════════════════════════════════════════════════════
#  REQUIREMENT 3
#  "If an item in the cart is out of stock at checkout time,
#   that item fails but other items in the cart still process."
# ══════════════════════════════════════════════════════════════════════════════

class TestCheckoutPartialFailure:

    def test_out_of_stock_item_causes_partial_failure(self):
        """
        PRECONDITION : Cart has laptop×1 (in stock) and hoverboard×1 (not stocked).
        ACTION       : Customer checks out.
        POSTCONDITION: Checkout returns partial failure.
                       Laptop order succeeds, hoverboard order fails.
        """
        cart.add_to_cart("frank@example.com", "laptop", 1)
        cart.add_to_cart("frank@example.com", "hoverboard", 1)   # not in stock

        result = checkout.checkout("frank@example.com")

        assert result.success is False
        assert len(result.order_ids) == 1      # laptop went through
        assert len(result.failures) == 1       # hoverboard failed
        assert result.failures[0]["item_id"] == "hoverboard"

    def test_failed_item_stays_in_cart_after_partial_checkout(self):
        """
        PRECONDITION : Cart has one good item and one out-of-stock item.
        ACTION       : Customer checks out (partial failure).
        POSTCONDITION: Cart still contains the failed item so the customer
                       can try again or remove it.
        """
        cart.add_to_cart("frank@example.com", "mouse", 3)
        cart.add_to_cart("frank@example.com", "hoverboard", 1)

        checkout.checkout("frank@example.com")

        remaining = cart.get_cart("frank@example.com")
        assert "hoverboard" in remaining       # still in cart
        assert "mouse" not in remaining        # successfully ordered, removed

    def test_successful_items_stock_is_reduced_despite_partial_failure(self):
        cart.add_to_cart("grace@example.com", "keyboard", 5)
        cart.add_to_cart("grace@example.com", "hoverboard", 1)

        checkout.checkout("grace@example.com")

        assert inventory.get_stock("keyboard") == 20   # 25 - 5, deducted

    def test_requesting_more_than_stock_causes_failure(self):
        """
        PRECONDITION : Cart requests 999 laptops, only 10 available.
        ACTION       : Checkout attempted.
        POSTCONDITION: That item fails; failure message mentions the quantity issue.
        """
        cart.add_to_cart("heidi@example.com", "laptop", 999)

        result = checkout.checkout("heidi@example.com")

        assert result.success is False
        assert len(result.failures) == 1
        assert "stock" in result.failures[0]["reason"].lower()


# ══════════════════════════════════════════════════════════════════════════════
#  REQUIREMENT 4
#  "Invalid customer inputs are rejected before any processing begins."
# ══════════════════════════════════════════════════════════════════════════════

class TestCheckoutInputValidation:

    def test_invalid_email_is_rejected(self):
        """
        PRECONDITION : Customer email is malformed (no @ sign).
        ACTION       : Checkout attempted.
        POSTCONDITION: Checkout fails immediately; no stock is touched,
                       no notification is sent.
        """
        # Manually set up cart state as if the email was valid
        cart._carts["notanemail"] = {"laptop": 1}

        result = checkout.checkout("notanemail")

        assert result.success is False
        assert inventory.get_stock("laptop") == 10   # unchanged
        assert len(notifications.get_sent()) == 0

    def test_two_different_customers_carts_are_independent(self):
        """
        PRECONDITION : Alice and Bob each have different items in their carts.
        ACTION       : Alice checks out.
        POSTCONDITION: Bob's cart is completely unaffected.
        """
        cart.add_to_cart("alice@example.com", "laptop", 1)
        cart.add_to_cart("bob@example.com", "mouse", 5)

        checkout.checkout("alice@example.com")

        bob_cart = cart.get_cart("bob@example.com")
        assert bob_cart == {"mouse": 5}   # Bob's cart untouched
