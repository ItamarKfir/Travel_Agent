# Running Tests

## Problem
When running tests directly with `python .\tests\test_google_places.py`, you may get:
```
ModuleNotFoundError: No module named 'app'
```

This happens because Python doesn't automatically add the parent directory to the Python path.

## Solutions

### Option 1: Run directly (Recommended - Now Fixed!)
The test files now automatically add the backend directory to the path:
```powershell
cd backend
python .\tests\test_google_places.py
python .\tests\test_yelp.py
```

### Option 2: Use pytest (Recommended for CI/CD)
From the `backend/` directory:
```powershell
cd backend
python -m pytest tests/test_google_places.py -v
python -m pytest tests/test_yelp.py -v
```

### Option 3: Set PYTHONPATH environment variable
From the `backend/` directory:
```powershell
cd backend
$env:PYTHONPATH="."; python .\tests\test_google_places.py
```

### Option 4: Run all tests with pytest
```powershell
cd backend
python -m pytest tests/ -v
```

## Before Running Tests

Make sure you have:
1. Installed dependencies: `pip install -r requirements.txt`
2. Set API keys in `.env` file in the `backend/` directory:
   ```
   GOOGLE_PLACES_API_KEY=your_key_here
   YELP_API_KEY=your_key_here
   ```

## Test Structure

- `test_google_places.py` - Tests for Google Places API integration
- `test_yelp.py` - Tests for Yelp API integration
- Both can be run standalone or with pytest

