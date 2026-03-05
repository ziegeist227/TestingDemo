# Week 7 Lab — Software Testing
## CSCI 4250 Software Engineering 1

Welcome to the lab. You will build and run tests for a small order management system in three structured steps.

---

## Quick Start

1. Open this folder in **VS Code** (`File → Open Folder → select this folder`)
2. Open a terminal: **`Ctrl + `` ` ``**
3. Install pytest: `pip install pytest`
4. Configure tests: **`Ctrl+Shift+P` → `Python: Configure Tests` → `pytest` → `.`**
5. Follow the instructions below in order

---

## The System Under Test

Five Python modules that work together:

```
src/
├── inventory.py      — tracks stock levels (get_stock, reduce_stock)
├── orders.py         — processes a single order (place_order)
├── notifications.py  — sends confirmation messages (send_confirmation)
├── cart.py           — manages a customer's shopping cart (add_to_cart, checkout)
└── checkout.py       — the "Place Order" feature (checkout) — coordinates all others
```

The dependency chain is:

```
checkout.py  →  cart.py
checkout.py  →  orders.py  →  inventory.py
                orders.py  →  notifications.py
```

---

## Lab Steps — Do These in Order

| Step | File | What you are learning |
|---|---|---|
| **Step 1** | `instructions/STEP1_INSTRUCTIONS.md` | Unit testing — test each module in isolation with mocks |
| **Step 2** | `instructions/STEP2_INSTRUCTIONS.md` | Feature testing — test a complete user-facing feature end-to-end |
| **Step 3** | `instructions/STEP3_INSTRUCTIONS.md` | Integration testing — wire all modules together, introduce a bug, watch it get caught |
| **Step 4** | `instructions/STEP4_INSTRUCTIONS.md` | System testing — discussion of what lower levels cannot catch |

---

## Running Tests (Quick Reference)

Open the VS Code terminal and use these commands from the project root.

**Step 1 — Unit tests only:**
```
pytest tests/test_step1_unit_inventory.py tests/test_step1_unit_orders.py -v
```

**Step 2 — Feature tests only:**
```
pytest tests/test_step2_feature.py -v
```

**Step 3 — Integration tests only:**
```
pytest tests/test_step3_integration.py -v
```

**Run everything at once:**
```
pytest -v
```

**Run with a short summary at the end:**
```
pytest -v --tb=short
```

---

## Reading Test Output

```
PASSED   — test ran and all assertions passed ✅
FAILED   — test ran but an assertion was wrong ❌
ERROR    — test could not even start (usually an import error)
```

When a test fails, pytest shows you:
- The file and line number
- The assertion that failed
- The **actual** value vs the **expected** value

Example:
```
AssertionError: assert 0 == 7
  Left:  actual result
  Right: what we expected
```

---

## VS Code Test Explorer

Click the **beaker icon** (🧪) in the left sidebar to open the Test Explorer. From there you can:
- See all tests organised by file and class
- Run individual tests by clicking ▶ next to them
- See pass/fail status with colour coding
- Click a failed test to jump straight to the failing line

---

## Folder Structure

```
lab/
├── README.md                             ← you are here
├── conftest.py                           ← path setup (do not edit)
├── src/
│   ├── inventory.py
│   ├── orders.py
│   ├── notifications.py
│   ├── cart.py                           ← added in Step 2
│   └── checkout.py                       ← added in Step 2
├── tests/
│   ├── test_step1_unit_inventory.py      ← Step 1
│   ├── test_step1_unit_orders.py         ← Step 1
│   ├── test_step2_feature.py             ← Step 2
│   └── test_step3_integration.py         ← Step 3
└── instructions/
    ├── STEP1_INSTRUCTIONS.md
    ├── STEP2_INSTRUCTIONS.md
    ├── STEP3_INSTRUCTIONS.md
    └── STEP4_INSTRUCTIONS.md
```

---

## If Something Goes Wrong

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'inventory'` | Make sure you opened the `lab/` folder in VS Code, not a subfolder. `conftest.py` must be in the root. |
| `ModuleNotFoundError: No module named 'pytest'` | Run `pip install pytest` in the terminal |
| Tests don't appear in the beaker panel | `Ctrl+Shift+P` → `Python: Configure Tests` → `pytest` → `.` |
| VS Code is using the wrong Python | `Ctrl+Shift+P` → `Python: Select Interpreter` → choose Python 3.x |
| `pytest` command not found | Try `python -m pytest -v` instead |
