# Python Version Compatibility

## Recommended Python Versions

This project is tested and works best with:
- **Python 3.11** (Recommended - used in Docker)
- **Python 3.12** (Also supported)

## Python 3.13 Compatibility

Python 3.13 is very new and some packages may not have full support yet. If you encounter build errors:

### Option 1: Use Python 3.11 or 3.12 (Recommended)

```bash
# Using pyenv
pyenv install 3.11.9
pyenv local 3.11.9

# Or use Docker (which uses Python 3.11)
docker-compose up --build
```

### Option 2: Update Package Versions for Python 3.13

If you must use Python 3.13, try installing newer package versions:

```bash
pip install --upgrade pip setuptools wheel
pip install "psycopg2-binary>=2.9.9" "pydantic>=2.6.0" "pydantic-core>=2.20.0"
pip install -r requirements.txt
```

### Option 3: Use Docker (Easiest)

Docker uses Python 3.11 which has full package support:

```bash
docker-compose up --build
```

## Known Issues with Python 3.13

1. **psycopg2-binary**: May need to build from source or use newer version
2. **pydantic-core**: Version 2.14.5 has issues, need 2.20.0+
3. **coverage**: May need newer version

## Quick Fix for Python 3.13

```bash
# Install latest compatible versions
pip install --upgrade pip setuptools wheel
pip install "psycopg2-binary>=2.9.9" "pydantic>=2.6.0" "pydantic-core>=2.20.0" "coverage>=7.4.0"
pip install -r requirements.txt
```

