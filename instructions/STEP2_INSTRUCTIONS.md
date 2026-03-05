# Step 2 — Feature / Functional Testing in VS Code
## CSCI 4250 Software Engineering 1 | Week 7 Lab

---

## What is a Feature Test?

A **feature test** (also called a functional test) verifies that a **complete user-facing feature** works correctly from end to end.

Think about what the *user* actually does — not what individual functions do internally. In our system, the user doesn't call `inventory.reduce_stock()` directly. They click **"Checkout"**. That one action triggers a chain of events across multiple modules:

```
Customer clicks Checkout
    → cart.get_cart()          reads what's in the cart
    → orders.place_order()     for each item:
         → inventory.get_stock()       checks availability
         → inventory.reduce_stock()    deducts the stock
         → notifications.send_confirmation()  sends a receipt
    → cart.clear_cart()        empties the cart on success
    → Customer sees "Order confirmed ✅"
```

A feature test verifies this entire chain produces the right outcome — without caring about the internals.

---

## How Feature Tests Differ From Unit Tests

| | Unit Tests (Step 1) | Feature Tests (Step 2) |
|---|---|---|
| Scope | One function | One complete user feature |
| Uses real modules? | ❌ Mocked | ✅ All real |
| Tests internal logic? | ✅ Yes | ❌ No — treats feature as black box |
| Written from? | Developer's perspective | User/requirements perspective |
| Failure tells you... | Which function broke | Which user scenario broke |

---

## New Files Added for This Step

Two new source files have been added to `src/`:

**`cart.py`** — a shopping cart. Customers add items before checkout.
```
add_to_cart(email, item_id, quantity) → bool
remove_from_cart(email, item_id) → bool
get_cart(email) → dict
clear_cart(email) → None
```

**`checkout.py`** — the feature module. Orchestrates cart + orders.
```
checkout(email) → CheckoutResult
```

Open both files and read them before running the tests. Notice that `checkout.py` doesn't contain any business logic of its own — it coordinates other modules. That is what makes it a *feature*: it's a workflow, not a calculation.

---

## The Requirements We Are Testing

Feature tests are written against **requirements**, not code. Here are the four requirements covered in `test_step2_feature.py`:

**REQ-1** — A customer with items in their cart can complete a checkout. On success, their order is confirmed and their cart is cleared.

**REQ-2** — A customer cannot check out with an empty cart.

**REQ-3** — If an item in the cart is out of stock at checkout time, that item fails but other in-stock items still process (partial checkout).

**REQ-4** — Invalid customer inputs are rejected before any processing begins.

---

## Read the Test File Before Running It

Open `tests/test_step2_feature.py`. Notice the structure of every test:

```python
def test_checkout_single_item_succeeds(self):
    """
    PRECONDITION : Customer has 1 item in cart, item is in stock.
    ACTION       : Customer checks out.
    POSTCONDITION: Checkout succeeds and returns an order ID.
    """
    cart.add_to_cart("alice@example.com", "laptop", 2)   # ARRANGE

    result = checkout.checkout("alice@example.com")      # ACT

    assert result.success is True                        # ASSERT
    assert len(result.order_ids) == 1
```

Every test has a **docstring** written as Precondition / Action / Postcondition — the same format from lecture, now applied to a full feature instead of a single function.

---

## Running the Feature Tests

In the VS Code terminal:

```
pytest tests/test_step2_feature.py -v
```

All 13 tests should pass:

```
tests/test_step2_feature.py::TestCheckoutHappyPath::test_checkout_single_item_succeeds PASSED
tests/test_step2_feature.py::TestCheckoutHappyPath::test_checkout_clears_cart_on_success PASSED
tests/test_step2_feature.py::TestCheckoutHappyPath::test_checkout_multi_item_cart_succeeds PASSED
...
===================== 13 passed in 0.10s =====================
```

---

## Run All Steps So Far

```
pytest tests/test_step1_unit_inventory.py tests/test_step1_unit_orders.py tests/test_step2_feature.py -v
```

Expected: **34 passed**

---

## A Feature Test Catches This — Unit Tests Cannot

Open `src/checkout.py` and find the partial failure block. Introduce a bug by deleting the two lines that put failed items back into the cart:

**Before (correct):**
```python
if failures:
    cart.clear_cart(customer_email)
    for f in failures:
        cart.add_to_cart(customer_email, f["item_id"], f["quantity"])
```

**After (buggy — delete the for loop):**
```python
if failures:
    cart.clear_cart(customer_email)
    # BUG: failed items are gone forever — customer loses them
```

Save the file, then run the unit tests:

```
pytest tests/test_step1_unit_inventory.py tests/test_step1_unit_orders.py -v
```

**Result: all 21 unit tests still pass.** The unit tests have no idea `checkout.py` even exists.

Now run the feature tests:

```
pytest tests/test_step2_feature.py -v
```

**One test fails immediately:**

```
FAILED ::TestCheckoutPartialFailure::test_failed_item_stays_in_cart_after_partial_checkout

AssertionError: assert 'hoverboard' in {}
```

The feature test caught a real user-facing regression: "the item I couldn't buy has vanished from my cart." The fix is to restore the deleted lines.

---

## What Feature Tests Tell You That Unit Tests Don't

| What to check | Unit test? | Feature test? |
|---|---|---|
| `reduce_stock()` returns correct bool | ✅ | — |
| `place_order()` validates email | ✅ | — |
| Checkout clears cart after success | ❌ | ✅ |
| Failed items remain in cart | ❌ | ✅ |
| Two customers' carts don't interfere | ❌ | ✅ |
| Confirmation sent per item on checkout | ❌ | ✅ |
| Partial order: stock only deducted for successes | ❌ | ✅ |

---

## Discussion Questions

1. Look at `test_two_different_customers_carts_are_independent`. Why is this important? What could go wrong in a multi-user system if sessions leaked into each other?

2. `TestCheckoutPartialFailure` covers a scenario where some items succeed and some fail. From a *user* perspective, is a partial checkout a good design? What would Amazon or Shopify do differently?

3. We have unit tests for `orders.py` and feature tests for `checkout.py`, but no unit tests for `checkout.py` itself. Should we write them? What would a unit test for `checkout.py` look like — and what would it check that the feature test doesn't?

4. Feature tests reset three modules in `setup_function()`. As a system grows to 20 modules, how do teams manage test setup at scale? What tools or patterns help?

---

## ✅ Step 2 Checklist

- [ ] Read `src/cart.py` and `src/checkout.py` before running the tests
- [ ] All 13 feature tests passed initially
- [ ] You introduced the bug in `checkout.py` and saw the feature test catch it
- [ ] You confirmed unit tests stayed green with the bug present
- [ ] You fixed the bug and all 34 tests pass
- [ ] You discussed at least one discussion question

**→ When ready, move to `STEP3_INSTRUCTIONS.md` (Integration Testing)**
