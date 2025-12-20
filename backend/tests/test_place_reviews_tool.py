"""
Tests for place reviews tool.

This test suite verifies that the place reviews tool correctly integrates
with Google Places and TripAdvisor APIs and formats output appropriately.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path so we can import app
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from dotenv import load_dotenv
from app.Tools.place_reviews_tool import get_place_reviews_from_apis

# Load environment variables
load_dotenv()


class TestPlaceReviewsTool:
    """Test suite for place reviews tool."""
    
    @pytest.fixture
    def google_api_key(self):
        """Get Google Places API key from environment."""
        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key:
            pytest.skip("GOOGLE_PLACES_API_KEY not set")
        return api_key
    
    @pytest.fixture
    def tripadvisor_api_key(self):
        """Get TripAdvisor API key from environment."""
        api_key = os.getenv("TRIPADVISOR_API_KEY")
        if not api_key:
            pytest.skip("TRIPADVISOR_API_KEY not set")
        return api_key
    
    def test_tool_with_valid_place_and_location(self, google_api_key, tripadvisor_api_key):
        """Test tool with a valid place name and location."""
        result = get_place_reviews_from_apis.invoke({
            "place_name": "Eiffel Tower",
            "location": "Paris, France"
        })
        
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Eiffel Tower" in result or "PLACE REVIEWS SUMMARY" in result
        assert "Google Places" in result
        assert "TripAdvisor" in result
    
    def test_tool_with_valid_place_no_location(self, google_api_key, tripadvisor_api_key):
        """Test tool with a valid place name but no location."""
        result = get_place_reviews_from_apis.invoke({
            "place_name": "Central Park",
            "location": None
        })
        
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Central Park" in result or "PLACE REVIEWS SUMMARY" in result
    
    def test_tool_with_invalid_place_name(self):
        """Test tool with invalid place name."""
        result = get_place_reviews_from_apis.invoke({
            "place_name": "",
            "location": None
        })
        
        assert result is not None
        assert "ERROR" in result
        assert "Invalid place_name" in result or "non-empty" in result
    
    def test_tool_with_nonexistent_place(self, google_api_key, tripadvisor_api_key):
        """Test tool with a place that doesn't exist."""
        result = get_place_reviews_from_apis.invoke({
            "place_name": "ThisPlaceDefinitelyDoesNotExist12345",
            "location": "Nowhere, Universe"
        })
        
        assert result is not None
        assert isinstance(result, str)
        # Should contain error messages or explanations
        assert "ERROR" in result or "not found" in result or "PLACE REVIEWS SUMMARY" in result
    
    def test_tool_output_format(self, google_api_key, tripadvisor_api_key):
        """Test that tool output is properly formatted."""
        result = get_place_reviews_from_apis.invoke({
            "place_name": "Times Square",
            "location": "New York, NY"
        })
        
        assert result is not None
        assert isinstance(result, str)
        # Check for expected sections
        assert "PLACE REVIEWS SUMMARY" in result
        assert "Google Places" in result
        assert "TripAdvisor" in result
        assert "SUMMARY:" in result
    
    def test_tool_error_handling(self):
        """Test that tool handles errors gracefully."""
        # Test with empty string
        result1 = get_place_reviews_from_apis.invoke({
            "place_name": "",
            "location": None
        })
        assert "ERROR" in result1
        
        # Test with None (should be handled by tool validation)
        # Note: LangChain tools typically handle None conversion, but we test edge cases
        result2 = get_place_reviews_from_apis.invoke({
            "place_name": "   ",  # Whitespace only
            "location": None
        })
        # Should either return error or attempt to search
        assert result2 is not None


if __name__ == "__main__":
    # Manual integration tests
    import sys
    
    google_api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    tripadvisor_api_key = os.getenv("TRIPADVISOR_API_KEY")
    
    if not google_api_key:
        print("WARNING: GOOGLE_PLACES_API_KEY not set in environment")
    if not tripadvisor_api_key:
        print("WARNING: TRIPADVISOR_API_KEY not set in environment")
    
    if not google_api_key and not tripadvisor_api_key:
        print("ERROR: At least one API key must be set")
        sys.exit(1)
    
    print("Testing Place Reviews Tool...")
    print("-" * 70)
    
    try:
        # Test 1: Valid place with location
        print("\n1. Testing with valid place and location (Eiffel Tower, Paris)...")
        result = get_place_reviews_from_apis.invoke({
            "place_name": "Eiffel Tower",
            "location": "Paris, France"
        })
        print(f"   Result length: {len(result)} characters")
        print(f"   First 500 chars:\n{result[:500]}...")
        assert "PLACE REVIEWS SUMMARY" in result or "ERROR" in result
        print("   [OK] Tool executed successfully")
        
        # Test 2: Valid place without location
        print("\n2. Testing with valid place without location (Central Park)...")
        result = get_place_reviews_from_apis.invoke({
            "place_name": "Central Park",
            "location": None
        })
        print(f"   Result length: {len(result)} characters")
        assert "PLACE REVIEWS SUMMARY" in result or "ERROR" in result
        print("   [OK] Tool executed successfully")
        
        # Test 3: Invalid place name
        print("\n3. Testing with invalid place name (empty string)...")
        result = get_place_reviews_from_apis.invoke({
            "place_name": "",
            "location": None
        })
        assert "ERROR" in result
        print(f"   [OK] Error handling works: {result[:200]}...")
        
        # Test 4: Nonexistent place
        print("\n4. Testing with nonexistent place...")
        result = get_place_reviews_from_apis.invoke({
            "place_name": "ThisPlaceDefinitelyDoesNotExist12345",
            "location": "Nowhere, Universe"
        })
        print(f"   Result length: {len(result)} characters")
        print(f"   First 300 chars:\n{result[:300]}...")
        assert result is not None
        print("   [OK] Error handling for nonexistent place works")
        
        print("\n" + "-" * 70)
        print("All manual tests passed!")
    
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
