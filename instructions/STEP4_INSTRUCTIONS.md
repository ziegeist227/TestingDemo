# Step 4 — System Testing Discussion
## CSCI 4250 Software Engineering 1 | Week 7 Lab

---

## No New Code — This Step is a Discussion

At the system testing level, we stop writing individual function tests and start asking:
**Does the whole system work as expected under real-world conditions?**

System tests are usually written against requirements, not code. They treat the entire application as a black box and test it from the outside — through a UI, an API, or a command-line interface.

Our order system is too small to have a real UI, but we can reason about what system tests would look like and what classes of problems they would catch that unit and integration tests cannot.

---

## What We Have Tested So Far

| Layer | What We Verified |
|---|---|
| Unit | Each function works correctly in isolation |
| Integration | `orders`, `inventory`, and `notifications` collaborate correctly |
| System | **Not yet tested** |

---

## Scenario: The System in Production

Imagine the order system is now a REST API. Real users call it over the internet. Multiple users may place orders at the same time. The system is connected to a real database and a real email provider.

---

## Problem 1 — Race Condition (Concurrent Orders)

**Situation:** Two customers — Alice and Bob — both visit the website at the same time. Only 1 laptop is left in stock.

**What happens with our current code?**

```
Alice's request:   get_stock("laptop") → 1   ✅ (enough)
Bob's request:     get_stock("laptop") → 1   ✅ (enough — read happens before Alice's write)
Alice's request:   reduce_stock("laptop", 1) → stock becomes 0
Bob's request:     reduce_stock("laptop", 1) → stock becomes -1  ❌
```

Both orders succeed. Stock goes negative. Two people have confirmation emails for a laptop that only one person will receive.

**Why didn't our tests catch this?**

Our tests run one request at a time, sequentially. There is no concept of simultaneous execution in `pytest` by default. This is a **concurrency bug** — it only appears when multiple things happen at the same time.

**What system-level solution would fix this?**

- Database-level row locking (pessimistic locking)
- Optimistic locking with version numbers
- A message queue that serialises all stock updates

**What does a system test for this look like?**

```python
# Pseudocode — not real pytest
def test_concurrent_orders_for_last_item():
    set_stock("laptop", 1)

    # Simulate two requests arriving simultaneously
    thread1 = Thread(target=place_order, args=("alice@example.com", "laptop", 1))
    thread2 = Thread(target=place_order, args=("bob@example.com",   "laptop", 1))
    thread1.start(); thread2.start()
    thread1.join();  thread2.join()

    # Exactly one should succeed
    successful_orders = count_successful_orders()
    assert successful_orders == 1
    assert get_stock("laptop") == 0  # never negative
```

---

## Problem 2 — Performance Under Load

**Situation:** A flash sale starts. 10,000 customers try to place orders in the first 60 seconds.

**What happens?**

- The server may run out of available threads/processes
- Each order check hits the inventory table — the database becomes a bottleneck
- Response times climb from 50ms to 10 seconds
- Timeouts cause some orders to partially succeed (payment taken, stock not reduced)

**Why didn't our tests catch this?**

Our tests each make one call. We never tested what happens under high load. This is a **performance/load testing** concern.

**What does a load test look like?**

Tools like **Locust** (Python) or **k6** are used to simulate thousands of concurrent users. A load test might specify:
- 1,000 virtual users placing orders simultaneously
- Average response time must be under 200ms
- No requests should time out

---

## Problem 3 — Email Delivery Failure

**Situation:** The email provider (SendGrid, Mailgun, etc.) is down. A customer places an order successfully but never receives a confirmation.

**What does our current `notifications.py` do?**

It prints to the console and stores in a list. It cannot fail. But the real notification module would call an external API that can return errors, time out, or be rate-limited.

**What should happen when the notification fails?**

Options:
1. Roll back the entire order (bad — customer loses their order)
2. Let the order succeed and log the failed notification for retry (better)
3. Put the notification in a reliable message queue (best — ensures eventual delivery)

**What does a system test for this look like?**

```python
# Pseudocode
def test_order_succeeds_even_when_email_provider_is_down():
    simulate_email_provider_outage()
    result = place_order_via_api("alice@example.com", "laptop", 1)
    assert result["status"] == "success"        # order went through
    assert result["order_id"] is not None
    assert email_retry_queue_length() == 1      # notification queued for retry
```

---

## Problem 4 — Security: Input Injection

**Situation:** A malicious user sends this order:

```json
{
  "email": "hacker@evil.com",
  "item_id": "'; DROP TABLE stock; --",
  "quantity": 1
}
```

**What does our current code do?**

`inventory.get_stock("'; DROP TABLE stock; --")` would return `0` (unknown item). Harmless in our version — but only because we use a Python dictionary, not a database.

In a real system with a SQL database and string concatenation:

```python
query = f"SELECT count FROM stock WHERE item_id = '{item_id}'"
# Becomes:
# SELECT count FROM stock WHERE item_id = ''; DROP TABLE stock; --'
```

The entire stock table gets deleted.

**System tests for security** include:
- SQL injection attempts
- XSS payloads in input fields
- Authentication bypass attempts
- Testing that API endpoints require valid tokens

---

## Problem 5 — Data Consistency Across a Restart

**Situation:** The server crashes mid-order after stock has been reduced but before the notification is sent. When the server restarts, the order does not exist in the database, but the stock was already decremented.

**What does our code do?**

Because everything is in memory (Python lists and dicts), a restart wipes everything. In a real system with persistent storage, this partial write is a critical bug.

**Solution:** Transactions — all steps of an order either complete together or are all rolled back. This is guaranteed by a database, not by application code alone.

---

## Summary: What Each Test Level Catches

| Bug Type | Unit Test | Integration Test | System Test |
|---|---|---|---|
| Wrong return type from a function | ❌ | ✅ (the bug we caught) | ✅ |
| Bad input validation | ✅ | ✅ | ✅ |
| Missing notification on failure | ✅ (with mock) | ✅ (real modules) | ✅ |
| Concurrent orders / race conditions | ❌ | ❌ | ✅ |
| Performance under 10,000 users | ❌ | ❌ | ✅ |
| Email provider outage handling | ❌ | ❌ | ✅ |
| SQL injection / security | ❌ | ❌ | ✅ |
| Data consistency after crash | ❌ | ❌ | ✅ |

No single test level is sufficient on its own. Each layer catches different classes of bugs.

---

## Discussion Questions

Work through these with your group. Be ready to share your answers in the class debrief.

**Q1.** In Problem 1 (race condition), both unit tests and integration tests passed. Does that mean the code is correct? What does "correct" mean at different testing levels?

**Q2.** Our `notifications.py` can never fail. How would you redesign `orders.py` so that a notification failure does not cause the customer to lose their order? Sketch the logic in plain English.

**Q3.** Look at the summary table. Three bugs are marked ❌ for unit tests but ✅ for system tests. What property do all three of those bugs share? Why can't unit tests see them?

**Q4.** Sommerville describes release testing as building confidence that the system is ready to ship. After completing unit, integration, and system testing, what would you still want to check before you let real customers use this order system?

**Q5.** In an Agile sprint, when would you run each level of testing? Would you automate all three? What would be the cost of automating system tests compared to unit tests?

---

## ✅ Step 3 Checklist

- [ ] Read through all five problem scenarios
- [ ] Answered at least two discussion questions as a group
- [ ] Ready to share one answer in the class debrief

---

## Final Terminal Check — Run Everything

Before the debrief, confirm the whole suite is clean:

```
pytest -v
```

Expected output:

```
tests/test_step1_unit_inventory.py    21 passed
tests/test_step1_unit_orders.py       10 passed
tests/test_step3_integration.py       13 passed
===================== 34 passed in 0.xx s =====================
```

If anything is failing, ask for help before the debrief starts.
