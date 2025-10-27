# A2IA CLI Keyboard Controls

## Interruption Controls

### Ctrl+C (^C)

**During Input:**
- Exits the CLI
- Shows "👋 Goodbye!" message

**During Inference:**
- Interrupts the current model response
- Stops thinking animation
- Shows red "⚠️  Interrupted" message
- Returns to prompt for next query

### Example Usage

```
You: Write me a very long essay about quantum physics

⠋ Thinking...
^C                          ← Press Ctrl+C here
⚠️  Interrupted

You: What is 2+2?           ← Ready for next query
```

## Other Controls

### /commands

- `/quit` or `/exit` - Exit the CLI
- `/clear` - Clear conversation history
- `/tools` - List available MCP tools

## Visual Formatting

**Thinking Animation:**
```
[blank line]
⠋ Thinking...
```

**After Tool Call:**
```
🔧 ToolName(args...)
   ↳ result
   
A2IA: Response continues here...
```

**Interrupted:**
```
⠋ Thinking...
^C
⚠️  Interrupted
```

## Implementation Notes

- Newline added before "Thinking..." for better spacing
- Red color used for interrupt message (\033[31m)
- Thinking animation properly stopped on interrupt
- Conversation history preserved after interrupt
- Label "A2IA:" not re-printed after tool results (continuous flow)

---

**Date:** 2025-10-27  
**Status:** Implemented

