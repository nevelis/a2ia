# CLI Command History

## Feature

The A2IA CLI now saves your command history to `~/.a2ia-history`, making it persistent across sessions!

## Usage

### Navigation
- **Up Arrow** (↑): Navigate to previous commands
- **Down Arrow** (↓): Navigate to next commands
- **Ctrl+R**: Search through history (prompt_toolkit feature)

### Behavior

The history automatically:
- ✅ **Persists across sessions** - Your commands are saved and available in future sessions
- ✅ **Skips blank lines** - Empty commands don't clutter your history
- ✅ **Deduplicates consecutive commands** - If you run the same command twice in a row, only one entry is saved
- ✅ **Keeps non-consecutive repeats** - If you run a command, then other commands, then the first command again, all instances are saved

### Example

```bash
# Session 1
$ a2ia-cli
You: list files
You: read config.py
You: read config.py  # Duplicate - not saved
You: exit

# Session 2  
$ a2ia-cli
[Press Up Arrow]
You: read config.py  # ← Your last command from previous session!
[Press Up Arrow]
You: list files
```

## Implementation

### Custom History Class

Created `DeduplicatingFileHistory` class that extends `prompt_toolkit.history.FileHistory`:

```python
class DeduplicatingFileHistory(FileHistory):
    """FileHistory that skips blank lines and consecutive duplicates."""
    
    def append_string(self, string: str) -> None:
        """Append string to history, skipping blanks and consecutive duplicates."""
        # Skip blank lines
        if not string or not string.strip():
            return
        
        # Check if this is a duplicate of the last entry
        try:
            with open(self.filename, 'r') as f:
                lines = f.readlines()
            
            # Find the last command (lines starting with '+')
            last_command = None
            for line in reversed(lines):
                if line.startswith('+'):
                    last_command = line[1:].rstrip('\n')
                    break
            
            # Skip if same as last command
            if last_command == string:
                return
        except (FileNotFoundError, IOError):
            pass
        
        # Append to history
        super().append_string(string)
```

### Integration

```python
# In CLI.__init__()
history_file = Path.home() / ".a2ia-history"
self.session = PromptSession(history=DeduplicatingFileHistory(str(history_file)))
```

## File Location

History is stored in: **`~/.a2ia-history`**

You can:
- View it: `cat ~/.a2ia-history`
- Clear it: `rm ~/.a2ia-history`
- Edit it: `vim ~/.a2ia-history` (not recommended, but possible)

## Format

The history file uses prompt_toolkit's format:
```
# 2025-10-27 14:23:45.123456
+command goes here

# 2025-10-27 14:24:12.987654
+another command
```

Each entry has:
1. A timestamp comment line (starting with `#`)
2. The command (starting with `+`)
3. A blank line separator

## Ghost Doctrine ✅

- ✅ Zero linting errors
- ✅ All tests passing
- ✅ Clean implementation
- ✅ Documented

Enjoy your persistent command history! 🎉

