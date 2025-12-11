# Testing Fix - pytest-flask Removal

## Issue
`ImportError: cannot import name 'FixtureDef' from 'pytest'` when running pytest.

## Root Cause
`pytest-flask==1.3.0` is incompatible with:
- Python 3.13
- Newer pytest versions (8.0+)

The `FixtureDef` class was moved to an internal module in newer pytest versions.

## Solution
Removed `pytest-flask` from requirements because:
1. It wasn't being used in any test files
2. Our `conftest.py` already provides Flask test fixtures manually
3. Manual fixtures are more flexible and don't require external plugins

## Changes Made
1. Removed `pytest-flask==1.3.0` from `requirements.txt`
2. Updated pytest to `>=8.0.0` (now using pytest 9.0.2)
3. Updated other test dependencies to use `>=` for flexibility

## Verification
```bash
cd backend
python -m pytest --version  # Should show pytest 9.0.2
python -m pytest tests/     # Should run all tests successfully
```

## Alternative (if you need pytest-flask)
If you specifically need pytest-flask features, you can:
1. Use Python 3.11 or 3.12 instead of 3.13
2. Wait for pytest-flask to release a Python 3.13 compatible version
3. Use manual fixtures (current approach - recommended)

