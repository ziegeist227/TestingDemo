# Step 1 — Unit Testing in VS Code
## CSCI 4250 Software Engineering 1 | Week 7 Lab

---

## What is a Unit Test?

A **unit test** checks one function or method **in complete isolation** — no database, no network, no other modules. If the function misbehaves, the test fails. Nothing else can interfere.

We test each module (`inventory`, `orders`) independently. When testing `orders`, we **mock** (fake) the `inventory` and `notifications` modules so that a bug in inventory cannot cause an orders test to fail.

---

## Project Structure

After unzipping the lab folder you should see:

```
lab/
├── conftest.py                        ← tells pytest where src/ is
├── src/
│   ├── inventory.py
│   ├── orders.py
│   └── notifications.py
└── tests/
    ├── test_step1_unit_inventory.py   ← YOU ARE HERE
    ├── test_step1_unit_orders.py      ← YOU ARE HERE
    ├── test_step2_integration.py      (Step 2 — do not run yet)
    └── test_step3_bug.py              (Step 3 — do not run yet)
```

---

## One-Time Setup (do this once at the start of lab)

### 1. Open the project in VS Code

1. Open **VS Code**
2. Go to **File → Open Folder**
3. Select the `lab` folder you unzipped

### 2. Open a terminal inside VS Code

Press **`` Ctrl + ` ``** (backtick) — this opens the integrated terminal at the bottom of the screen.

### 3. Check Python is installed

Type this and press Enter:

```
python --version
```

You should see something like `Python 3.11.x`. If you see an error, raise your hand.

### 4. Install pytest

```
pip install pytest
```

Wait for it to finish. You should see `Successfully installed pytest-...`

### 5. Tell VS Code to use pytest

1. Press **`Ctrl + Shift + P`** to open the Command Palette
2. Type **`Python: Configure Tests`** and press Enter
3. Select **`pytest`**
4. Select **`.`** (the root folder — where `conftest.py` lives)

VS Code will now show a **beaker icon** (🧪) in the left sidebar.

---

## Reading the Source Code First (5 minutes)

Before writing or running any tests, **read the code**. Open `src/inventory.py`.

Notice:
- `get_stock(item_id)` → returns an `int` (the count)
- `reduce_stock(item_id, quantity)` → returns `True` on success, `False` if not enough stock, raises `ValueError` if quantity ≤ 0
- `reset_stock()` → resets everything back to defaults (we call this before every test)

Open `src/orders.py` and trace the flow of `place_order()`:

```
validate inputs
  → check stock (calls inventory.get_stock)
  → reduce stock (calls inventory.reduce_stock)
  → send notification (calls notifications.send_confirmation)
  → return OrderResult
```

---

## Running the Unit Tests

### Option A — Using the VS Code Test Explorer (recommended for beginners)

1. Click the **beaker icon** (🧪) in the left sidebar
2. You will see a tree of all test files and test functions
3. Click the **▶ Run All Tests** button at the top of the panel

Each test shows:
- ✅ **green check** = passed
- ❌ **red X** = failed  
- Click any failed test to see the exact line that failed and why

### Option B — Using the terminal

Run only the inventory unit tests:
```
pytest tests/test_step1_unit_inventory.py -v
```

Run only the orders unit tests:
```
pytest tests/test_step1_unit_orders.py -v
```

Run both step 1 files together:
```
pytest tests/test_step1_unit_inventory.py tests/test_step1_unit_orders.py -v
```

The `-v` flag means **verbose** — it prints each individual test name and PASSED/FAILED next to it.

---

## What You Should See

All tests in both step 1 files should pass:

```
tests/test_step1_unit_inventory.py::TestGetStock::test_returns_correct_count_for_known_item PASSED
tests/test_step1_unit_inventory.py::TestGetStock::test_returns_zero_for_unknown_item PASSED
...
tests/test_step1_unit_orders.py::TestPlaceOrderLogic::test_order_succeeds_when_stock_available PASSED
...
===================== 21 passed in 0.12s =====================
```

**If you see red:** Read the error message carefully. It shows you the exact assertion that failed and the actual vs expected values.

---

## Understanding the Test Code

Open `test_step1_unit_inventory.py` and look at this test:

```python
def test_happy_path_returns_true(self):
    # ARRANGE: laptop stock = 10 (reset happened in setup_function)
    # ACT: reduce by 3
    result = inventory.reduce_stock("laptop", 3)
    # ASSERT: should succeed
    assert result is True
```

Every test follows **ARRANGE → ACT → ASSERT**:
- **ARRANGE**: Set up the starting state (`setup_function()` handles this for us)
- **ACT**: Call the function being tested
- **ASSERT**: Check the result is what we expected

Now look at `test_step1_unit_orders.py` and find this test:

```python
@patch("orders.inventory")
@patch("orders.notifications")
def test_order_fails_when_stock_insufficient(self, mock_notif, mock_inv):
    mock_inv.get_stock.return_value = 1   # fake: only 1 in stock
    result = orders.place_order("alice@example.com", "laptop", 5)
    assert result.success is False
    mock_inv.reduce_stock.assert_not_called()   # must NOT have tried to reduce
```

The `@patch(...)` decorators **replace** the real `inventory` and `notifications` modules with fakes for the duration of this test. This means:
- We control exactly what `get_stock()` returns
- We can verify that `reduce_stock()` was or wasn't called
- A real bug in `inventory.py` cannot interfere with this test

---

## Discussion Questions (discuss with your group)

1. The unit tests for `orders` use mocks. What is the risk of relying only on mocked tests? What could still go wrong in production?

2. Look at `test_reduce_all_stock_leaves_zero`. Why is ordering exactly the full available amount an important edge case?

3. `test_insufficient_stock_does_not_change_count` checks that stock is **unchanged** after a failed reduction. Why is this important? What would happen to a customer if this check didn't exist?

4. In `test_order_fails_when_stock_insufficient`, we assert `mock_inv.reduce_stock.assert_not_called()`. Why should `reduce_stock` never be called when there is insufficient stock?

---

## ✅ Step 1 Checklist

Before moving to Step 2, confirm:

- [ ] All 21 unit tests pass (green in Test Explorer or terminal)
- [ ] You understand the difference between the inventory and orders unit tests
- [ ] You understand why `@patch` is used in the orders tests
- [ ] You have discussed at least one discussion question with your group

**→ When ready, move to `STEP2_INSTRUCTIONS.md`**
