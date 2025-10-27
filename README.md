# dini-test-poc

Best Hooks for Proactive Summarisation

  Option 1: BeforeModelCallEvent (BEST for your use case)

  - ✅ Fires before each model call during the agentic loop
  - ✅ Allows you to modify messages before they're sent to the model
  - ✅ Perfect timing: reduces context right before it's needed
  - ✅ Reduces token costs immediately

  Option 2: MessageAddedEvent

  - ✅ Fires whenever messages are added to history
  - ✅ Continuous visibility into conversation growth
  - ⚠️ Might fire too frequently (after every message)
  - ⚠️ Would need throttling to avoid overhead

  Option 3: AfterToolCallEvent

  - ✅ Fires after each tool execution
  - ✅ Good frequency (once per tool use)
  - ⚠️ Doesn't prevent sending large context to the model

  Recommendation: Use BeforeModelCallEvent because:
  1. It fires at the perfect time (right before model calls)
  2. You can modify the messages before they're sent
  3. It happens during the loop (every time the agent calls the model for the next action)
  4. Saves tokens immediately