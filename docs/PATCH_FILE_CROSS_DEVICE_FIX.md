# PatchFile Cross-Device Fix

## Problem

When the LLM tried to use `PatchFile` to fix syntax errors, it failed with:

```
🔧 PatchFile(diff='--- a/get_weather.py\n+++ b/get_weather.py\n@@ -20,1...', path='/get_weather.py')
   ↳ success: False
     stderr: [Errno 18] Invalid cross-device link
```

**Root Cause:**  
The `patch_file` function uses `tempfile.NamedTemporaryFile()` which creates temporary files in `/tmp` by default. When it tried to use `os.replace()` to move the temp file to the workspace (on a different filesystem), Python raised "Invalid cross-device link" error.

## Technical Details

### Why It Fails

`os.replace()` and `os.rename()` use the `renameat2()` system call which:
- ✅ Works within the same filesystem (atomic operation)
- ❌ Fails across different filesystems (can't link across devices)

```python
# Original code (broken)
with tempfile.NamedTemporaryFile('w', delete=False) as tmp:
    tmp.write(new_content)
    tmp_path = tmp.name  # /tmp/tmpXXXXXX

os.replace(tmp_path, file_path)  # ❌ Fails if /tmp and workspace on different filesystems
```

### Why It Happens

Common scenarios where `/tmp` is on a different filesystem:
- `/tmp` is a `tmpfs` mount (RAM-based)
- `/tmp` is on a separate partition
- Workspace is on a network filesystem (NFS, SMB)
- Workspace is on a different disk

## Solution

Replace `os.replace()` with `shutil.move()` which automatically handles cross-device moves:

```python
# Fixed code
with tempfile.NamedTemporaryFile('w', delete=False) as tmp:
    tmp.write(new_content)
    tmp_path = tmp.name

# Use shutil.move() instead of os.replace() to handle cross-device moves
# When temp file is on different filesystem (e.g., /tmp), os.replace() fails
shutil.move(tmp_path, file_path)  # ✅ Works across filesystems
```

### How shutil.move() Works

`shutil.move()` is smarter:
1. **Try rename first** - Attempts `os.rename()` for speed (atomic)
2. **Fall back to copy+delete** - If rename fails (cross-device), it:
   - Copies the file to the destination
   - Deletes the source file
   - Preserves permissions and metadata

This ensures the operation succeeds regardless of filesystem boundaries.

## Impact

### Before Fix
```
✗ PatchFile fails with "Invalid cross-device link"
✗ LLM cannot apply diffs to fix files
✗ Manual intervention required
```

### After Fix
```
✅ PatchFile works across all filesystem configurations
✅ LLM can apply diffs seamlessly
✅ Same atomic guarantees within filesystem
✅ Automatic fallback for cross-filesystem
```

## Testing

All existing patch file tests continue to pass:
- ✅ 8 patch file API tests
- ✅ 5 comprehensive patch tests
- **13/13 tests passing**

The fix is transparent - existing functionality unchanged, just more robust.

## Files Changed

1. **`a2ia/tools/filesystem_tools.py`**
   - Added `import shutil`
   - Changed line 184: `os.replace(tmp_path, file_path)` → `shutil.move(tmp_path, file_path)`
   - Added comment explaining the fix

## Ghost Doctrine ✅

- ✅ All tests passing (13/13 patch file tests)
- ✅ Zero linting errors
- ✅ No breaking changes
- ✅ Production bug fixed
- ✅ Documented

## Bottom Line

The LLM tried to help fix syntax errors but couldn't apply patches due to filesystem boundaries. Now it can! `shutil.move()` handles both cases:
- **Same filesystem**: Fast atomic rename
- **Different filesystem**: Safe copy+delete

Perfect fix for a perfect assistant! 🎉

