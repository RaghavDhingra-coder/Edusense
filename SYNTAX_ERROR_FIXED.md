# Syntax Error Fixed ✅

## Error

```
File "/Users/raghavdhingra/EduSence-ai/integrated_server.py", line 1152
global upload_worker
^
SyntaxError: name 'upload_worker' is used prior to global declaration
```

## Cause

Python requires `global` declarations to be at the **start of a function**, before the variable is used. The code had `global upload_worker` declarations in the middle of functions, after the variable was already referenced.

## Fix

Moved all `global upload_worker` declarations to the start of their respective functions:

### 1. `get_camera_stats()` function
**Before:**
```python
def get_camera_stats():
    try:
        cam_sys = get_camera_system()
        
        if cam_sys is None:
            global upload_worker  # ❌ Too late!
            if upload_worker and upload_worker.running:
                ...
```

**After:**
```python
def get_camera_stats():
    try:
        global upload_worker  # ✅ At the start
        
        cam_sys = get_camera_system()
        
        if cam_sys is None:
            if upload_worker and upload_worker.running:
                ...
```

### 2. `analyze_classroom()` function
**Before:**
```python
def analyze_classroom():
    try:
        logger.info("Starting analysis...")
        
        # ... many lines of code ...
        
        if len(session_images) == 0:
            global upload_worker  # ❌ Too late!
            if upload_worker and upload_worker.running:
                ...
```

**After:**
```python
def analyze_classroom():
    try:
        global upload_worker  # ✅ At the start
        
        logger.info("Starting analysis...")
        
        # ... many lines of code ...
        
        if len(session_images) == 0:
            if upload_worker and upload_worker.running:
                ...
```

## Verification

✅ **Syntax check passed:**
```bash
python3 -m py_compile integrated_server.py
# Exit code: 0
```

✅ **Import test passed:**
```bash
python3 -c "import integrated_server; print('✅ Import successful')"
# Output: ✅ Import successful
```

✅ **Server can now start:**
```bash
python3 integrated_server.py
# Server starts successfully
```

## Files Modified

- `integrated_server.py` (2 functions fixed)

## Status

✅ **FIXED** - Server can now start without syntax errors

## Next Steps

1. Start the server:
   ```bash
   python3 integrated_server.py
   ```

2. Test the analytics flow:
   - Start camera
   - Let it run for 1-2 minutes
   - Stop camera
   - Wait 60 seconds
   - Click "Analyze"

3. Run the test script:
   ```bash
   python3 test_upload_flow.py
   ```
