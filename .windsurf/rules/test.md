The Flow Test Structure (AAA Pattern)
Every test for your flow should follow this structure strictly:
pseudocode — template for every flow test:

  test "specific scenario name that describes business behavior":

      ── ARRANGE ──────────────────────────────────────────
      set up only the state this test needs
      create fake versions of all external dependencies
      configure fakes to return specific data for this scenario
      wire everything together

      ── ACT ──────────────────────────────────────────────
      call exactly ONE entry point
      capture the result

      ── ASSERT ───────────────────────────────────────────
      assert the return value (if any)
      assert side effects on fakes (was DB called? with what?)
      assert NO unexpected interactions happened
Rule: One test = one scenario = one reason to fail. If a test can fail for two different reasons, split it into two tests.
=======
Characterization Tests — Lock Current Behavior First
Before you write any "proper" tests, write characterization tests. These answer: "What does the code actually do right now?"
pseudocode:

  test "characterize: what does processOrder return for valid input?":
      result = processOrder(knownValidInput)
      assert result == whatever_it_actually_returns_right_now

  test "characterize: what does processOrder do when user not found?":
      result = processOrder(inputWithBadUserId)
      assert result == whatever_it_actually_does_right_now
      ← even if it does something wrong, capture it
         you'll fix behavior later, under test coverage
These tests are your safety net. They let you know the moment you accidentally change existing behavior while adding seams.