# CLI Interrupt Fix - Immediate Response to Ctrl+C

## Problem

When pressing `Ctrl+C` during the "Thinking..." animation (before the LLM sends the first token), the CLI would hang and not respond immediately. The interrupt would only take effect after the first token arrived from the LLM.

```
You: Hey how are you                                              
                                                                  
⠙ Thinking...^C^C^C^C  [hangs here waiting for first token]

⚠️  Interrupted  [only shows after LLM responds]
```

## Root Cause

The interrupt check was inside the `async for chunk in stream:` loop, which meant:
1. User presses `Ctrl+C`
2. Signal handler sets `_interrupt_requested = True`
3. But the loop is blocked waiting for the first chunk from the LLM
4. Interrupt can't be detected until a chunk arrives

## Solution

Refactored the inference processing to use **concurrent tasks with asyncio.wait()**:

1. **Monitor Task**: Polls the `_interrupt_requested` flag every 50ms
2. **Stream Task**: Consumes the LLM stream
3. **asyncio.wait()**: Returns as soon as either task completes

When `Ctrl+C` is pressed:
1. Signal handler sets `_interrupt_requested = True`
2. Monitor task detects it within 50ms
3. Monitor task cancels the stream task
4. Interrupt message is displayed immediately

## Key Changes

### 1. Separate Stream Consumption

Moved all stream processing logic into `_consume_stream()` method that can be cancelled:

```python
async def _consume_stream(self, stream, thinking, state_dict):
    """Consume stream and process chunks."""
    async for chunk in stream:
        chunk_type = chunk.get('type')
        # ... process all chunk types ...
```

### 2. Interrupt Monitoring Task

Added background task that monitors for interrupts:

```python
async def _monitor_interrupt(self, stream_task):
    """Monitor for interrupt requests and cancel stream task."""
    while not self._interrupt_requested and not stream_task.done():
        await asyncio.sleep(0.05)  # Check every 50ms
    
    if self._interrupt_requested and not stream_task.done():
        stream_task.cancel()
```

### 3. Concurrent Execution

Run both tasks concurrently and respond to whichever completes first:

```python
# Create tasks for stream consumption and interrupt monitoring
stream_task = asyncio.create_task(self._consume_stream(stream, thinking, state_dict))
monitor_task = asyncio.create_task(self._monitor_interrupt(stream_task))

# Wait for stream to complete or be interrupted
done, pending = await asyncio.wait(
    [stream_task, monitor_task],
    return_when=asyncio.FIRST_COMPLETED
)

# Cancel any remaining tasks
for task in pending:
    task.cancel()

# Check if we were interrupted
if self._interrupt_requested or stream_task.cancelled():
    await thinking.stop()
    print("\n\033[31m⚠️  Interrupted\033[0m\n")
    return
```

## Behavior Now

**Before the fix:**
- `Ctrl+C` during "Thinking..." → Hangs until first LLM token → Shows interrupt

**After the fix:**
- `Ctrl+C` during "Thinking..." → Responds within 50ms → Shows interrupt immediately

## Implementation Details

### Signal Handler (unchanged)
```python
def _handle_sigint(self, signum, frame):
    """Handle SIGINT (Ctrl+C) signal."""
    if self._processing_inference:
        self._interrupt_requested = True  # Set flag, don't raise
    else:
        raise KeyboardInterrupt()  # At prompt, exit
```

### State Tracking
- `_processing_inference`: True when actively processing LLM response
- `_interrupt_requested`: Set by signal handler, checked by monitor task

### Responsiveness
- Monitor task polls every **50ms** (imperceptible to users)
- Balance between responsiveness and CPU usage
- Could be tuned lower (e.g., 25ms) if needed

## Files Changed

1. **`a2ia/cli/interface.py`**
   - Added `_monitor_interrupt()` method
   - Added `_consume_stream()` method  
   - Refactored `_process_inference()` to use concurrent tasks
   - Moved stream processing logic into separate method

## Testing

✅ All tests pass (7/7 vLLM client tests)
✅ Zero linting errors
✅ Manual testing:
   - `Ctrl+C` at prompt → Exits immediately
   - `Ctrl+C` during thinking → Interrupts within 50ms
   - `Ctrl+C` during streaming → Interrupts immediately
   - Normal operation unaffected

## Ghost Doctrine ✅

- ✅ Zero warnings
- ✅ Zero linting errors  
- ✅ All tests passing
- ✅ Clean refactoring
- ✅ Clear documentation

Now `Ctrl+C` provides **instant feedback** to the user, no more hanging! 🎉

