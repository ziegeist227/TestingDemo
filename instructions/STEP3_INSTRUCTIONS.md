# Step 3 — Integration Testing in VS Code
## CSCI 4250 Software Engineering 1 | Week 7 Lab

---

## What is an Integration Test?

An **integration test** wires the real modules together — no mocking, no fakes. We are testing whether `orders`, `inventory`, and `notifications` **collaborate correctly** when they interact with each other.

| | Unit Tests | Integration Tests |
|---|---|---|
| Uses real `inventory`? | ❌ No (mocked) | ✅ Yes |
| Uses real `notifications`? | ❌ No (mocked) | ✅ Yes |
| Tests function logic? | ✅ Yes | ✅ Yes |
| Tests module interfaces? | ❌ No | ✅ Yes |
| Can catch "wrong data format between modules"? | ❌ No | ✅ Yes |

---

## Before You Start

Make sure all Step 1 and Step 2 tests still pass:

```
pytest tests/test_step1_unit_inventory.py tests/test_step1_unit_orders.py -v
```

You should see **21 passed**. If anything is failing, fix it before continuing.

---

## Running the Integration Tests

In the VS Code terminal:

```
pytest tests/test_step3_integration.py -v
```

You should see all tests pass — **for now**.

```
tests/test_step3_integration.py::TestOrdersInventoryIntegration::test_successful_order_reduces_stock_by_correct_amount PASSED
tests/test_step3_integration.py::TestOrdersInventoryIntegration::test_order_for_unavailable_item_leaves_stock_unchanged PASSED
...
===================== 13 passed in 0.08s =====================
```

Keep this terminal output visible — you will need it again in a moment.

---

## Introducing a Bug (live demo — instructor leads)

We are going to **deliberately break** `inventory.py` to simulate a real interface bug.

### What kind of bug are we introducing?

`reduce_stock()` is supposed to return `True` when it succeeds and `False` when it fails. The orders module relies on this contract:

```python
# In orders.py:
ok = inventory.reduce_stock(item_id, quantity)
if not ok:
    return OrderResult(False, "Stock reduction failed unexpectedly")
```

We will change `reduce_stock()` so that instead of returning `True`, it returns the **remaining stock count**. This seems harmless — `10`, `7`, `3` are all truthy — but watch what happens at the edge case where the remaining count is `0`.

### Make the change

Open `src/inventory.py`. Find `reduce_stock()` and change the last two lines from this:

```python
    _stock[item_id] = current - quantity
    return True                             # ← ORIGINAL
```

To this:

```python
    _stock[item_id] = current - quantity
    return _stock[item_id]                  # ← BUG: returns int, not bool
```

Save the file (`Ctrl + S`).

---

## Run the Unit Tests After the Bug

```
pytest tests/test_step1_unit_inventory.py tests/test_step1_unit_orders.py -v
```

**What do you see?** All tests still pass.

```
===================== 21 passed in 0.12s =====================
```

This is the key insight: **unit tests do not always catch interface bugs.** The inventory unit tests only check that the function works on its own. The orders unit tests use a mocked inventory, so they never even call the real `reduce_stock()`.

---

## Run the Integration Tests After the Bug

```
pytest tests/test_step3_integration.py -v
```

**Now you should see a failure:**

```
FAILED tests/test_step3_integration.py::TestOrdersInventoryIntegration::test_ordering_exact_remaining_stock_empties_item

FAILED - AssertionError: Order should succeed when requesting exactly available stock.
  Got: success=False, message='Stock reduction failed unexpectedly'
  Hint: check what reduce_stock() returns when stock hits zero.
```

### Why did this fail?

Walk through what happens when a customer orders all 10 laptops:

1. `orders.place_order("dana@example.com", "laptop", 10)` is called
2. `inventory.get_stock("laptop")` → returns `10` ✅
3. `inventory.reduce_stock("laptop", 10)` is called
4. Inside `reduce_stock`: `_stock["laptop"] = 10 - 10 = 0`
5. **BUG**: returns `0` instead of `True`
6. Back in `orders.py`: `ok = 0` → `if not ok` → `True` → **order fails!**

The customer tried to order something that was in stock, paid, and got told their order failed. And the unit tests never saw it coming.

---

## Run the Full Test Suite

```
pytest -v
```

You will see a clear picture of what passed and what failed:

```
tests/test_step1_unit_inventory.py ...........  PASSED  (11 tests)
tests/test_step1_unit_orders.py ..........      PASSED  (10 tests)
tests/test_step3_integration.py ....F........   1 FAILED
```

---

## Fix the Bug

Go back to `src/inventory.py` and restore the correct return value:

```python
    _stock[item_id] = current - quantity
    return True                             # ← FIXED
```

Save the file and run everything again:

```
pytest -v
```

All tests should now pass.

```
===================== 34 passed in 0.15s =====================
```

---

## Understanding the Integration Test Code

Open `test_step3_integration.py` and look at the setup:

```python
def setup_function():
    inventory.reset_stock()
    notifications.clear()
```

We reset **both** modules before every test. This is more work than in the unit tests (where we only reset inventory). Integration tests touch more state, so we need to clean up more carefully.

Now look at the full end-to-end test:

```python
def test_complete_happy_path(self):
    result = orders.place_order("frank@example.com", "laptop", 3)

    assert result.success is True
    assert result.order_id is not None

    assert inventory.get_stock("laptop") == 7   # 10 - 3

    sent = notifications.get_sent()
    assert len(sent) == 1
    assert sent[0]["email"] == "frank@example.com"
    assert sent[0]["order_id"] == result.order_id
```

A single test is checking **three different side-effects** of one action. This is normal in integration testing — you are verifying that the whole collaboration worked, not just that one function returned the right value.

---

## Discussion Questions (discuss with your group)

1. The bug we introduced changed a return type from `bool` to `int`. The function signature still said `-> bool`. Why didn't Python warn us about this? What tool might catch it?

2. Look at `test_failed_order_sends_no_notification`. Why is it important to assert that notifications were NOT sent, not just that the order failed?

3. We reset both modules in `setup_function()`. What would happen if we forgot to call `notifications.clear()` between tests? Try it: remove that call and run the tests. What breaks?

4. The unit tests for orders used `mock_inv.reduce_stock.assert_not_called()`. The integration test `test_order_for_unavailable_item_leaves_stock_unchanged` checks the same thing differently — by reading the actual stock count. Which approach do you prefer, and why?

---

## ✅ Step 2 Checklist

- [ ] All 13 integration tests passed initially
- [ ] You introduced the bug and saw exactly one integration test fail
- [ ] You confirmed the unit tests still passed with the bug present
- [ ] You fixed the bug and all 34 tests passed
- [ ] You discussed at least one discussion question with your group

**→ When ready, move to `STEP4_INSTRUCTIONS.md`**
