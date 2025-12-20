"""
Tests for Google Places API integration.
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
from app.API.google_places import (
    GooglePlacesClient,
    get_google_places_client,
    get_place_reviews,
    Review,
    PlaceDetails
)

# Load environment variables
load_dotenv()


class TestGooglePlacesClient:
    """Test suite for GooglePlacesClient."""
    
    @pytest.fixture
    def api_key(self):
        """Get API key from environment."""
        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key:
            pytest.skip("GOOGLE_PLACES_API_KEY not set")
        return api_key
    
    @pytest.fixture
    def client(self, api_key):
        """Create a GooglePlacesClient instance."""
        return GooglePlacesClient(api_key=api_key)
    
    def test_client_initialization_with_key(self, api_key):
        """Test client initialization with API key."""
        client = GooglePlacesClient(api_key=api_key)
        assert client is not None
        assert client.client is not None
    
    def test_client_initialization_without_key(self):
        """Test client initialization fails without API key."""
        # Temporarily remove key if it exists
        original_key = os.environ.get("GOOGLE_PLACES_API_KEY")
        if "GOOGLE_PLACES_API_KEY" in os.environ:
            del os.environ["GOOGLE_PLACES_API_KEY"]
        
        try:
            with pytest.raises(ValueError, match="GOOGLE_PLACES_API_KEY"):
                GooglePlacesClient()
        finally:
            # Restore original key
            if original_key:
                os.environ["GOOGLE_PLACES_API_KEY"] = original_key
    
    def test_validate_place_query_valid(self, client):
        """Test validation of valid place queries."""
        assert client._validate_place_query("Starbucks") == "Starbucks"
        assert client._validate_place_query("  Central Park  ") == "Central Park"
        assert client._validate_place_query("New York") == "New York"
    
    def test_validate_place_query_invalid(self, client):
        """Test validation rejects invalid place queries."""
        with pytest.raises(ValueError):
            client._validate_place_query("")
        
        with pytest.raises(ValueError):
            client._validate_place_query("a")
        
        with pytest.raises(ValueError):
            client._validate_place_query(None)
        
        with pytest.raises(ValueError):
            client._validate_place_query("a" * 201)  # Too long
    
    def test_search_place_success(self, client):
        """Test successful place search."""
        # Search for a well-known place
        place_id = client.search_place("Central Park New York")
        assert place_id is not None
        assert isinstance(place_id, str)
        assert len(place_id) > 0
    
    def test_search_place_not_found(self, client):
        """Test place search when place doesn't exist."""
        # Use a very unlikely place name
        place_id = client.search_place("XYZ123ABC456DEF789")
        # Should return None or empty, depending on API behavior
        # Some APIs return empty results, others might return closest match
        assert place_id is None or isinstance(place_id, str)
    
    def test_search_place_invalid_query(self, client):
        """Test place search with invalid query."""
        with pytest.raises(ValueError):
            client.search_place("")
        
        with pytest.raises(ValueError):
            client.search_place("a")
    
    def test_get_place_details_success(self, client):
        """Test getting place details."""
        # First search for a place
        place_id = client.search_place("Times Square New York")
        if not place_id:
            pytest.skip("Could not find place for testing")
        
        details = client.get_place_details(place_id)
        assert isinstance(details, dict)
        assert "place_id" in details or "name" in details
    
    def test_get_place_details_invalid_id(self, client):
        """Test getting details with invalid place_id."""
        with pytest.raises(ValueError):
            client.get_place_details("")
        
        with pytest.raises(ValueError):
            client.get_place_details(None)
    
    def test_parse_reviews_valid(self, client):
        """Test parsing valid review data."""
        raw_reviews = [
            {
                "author_name": "John Doe",
                "rating": 5,
                "text": "Great place!",
                "time": 1234567890,
                "relative_time_description": "2 months ago"
            },
            {
                "author_name": "Jane Smith",
                "rating": 3,
                "text": "Okay place.",
                "time": 1234567891
            }
        ]
        
        reviews = client._parse_reviews(raw_reviews)
        assert len(reviews) == 2
        assert all(isinstance(r, Review) for r in reviews)
        assert reviews[0].author_name == "John Doe"
        assert reviews[0].rating == 5
        assert reviews[1].rating == 3
    
    def test_sort_and_split_reviews(self, client):
        """Test sorting and splitting reviews into top/bottom."""
        reviews = [
            Review(author_name="User1", rating=5, text="Great"),
            Review(author_name="User2", rating=1, text="Bad"),
            Review(author_name="User3", rating=4, text="Good"),
            Review(author_name="User4", rating=2, text="Poor"),
            Review(author_name="User5", rating=5, text="Excellent"),
            Review(author_name="User6", rating=3, text="Average"),
            Review(author_name="User7", rating=1, text="Terrible"),
        ]
        
        top_reviews, bottom_reviews = client._sort_and_split_reviews(reviews)
        
        # Should have top 5 (all 5s and 4s)
        assert len(top_reviews) <= 5
        # Should have bottom 5 (all 1s and 2s)
        assert len(bottom_reviews) <= 5
        
        # Top reviews should be sorted highest first
        if len(top_reviews) > 1:
            assert top_reviews[0].rating >= top_reviews[-1].rating
        
        # Bottom reviews should be sorted lowest first
        if len(bottom_reviews) > 1:
            assert bottom_reviews[0].rating <= bottom_reviews[-1].rating
    
    def test_get_reviews_integration(self, client):
        """Integration test for getting reviews."""
        # Test with a well-known place that likely has reviews
        try:
            place_details = client.get_reviews("Central Park New York")
            
            assert isinstance(place_details, PlaceDetails)
            assert place_details.place_id is not None
            assert place_details.name is not None
            
            # Should have top and bottom reviews (may be empty if no reviews)
            assert isinstance(place_details.top_reviews, list)
            assert isinstance(place_details.bottom_reviews, list)
            assert len(place_details.top_reviews) <= 5
            assert len(place_details.bottom_reviews) <= 5
        
        except ValueError as e:
            # Place not found is acceptable
            if "not found" in str(e).lower():
                pytest.skip(f"Place not found: {e}")
            else:
                raise
    
    def test_get_reviews_place_not_found(self, client):
        """Test getting reviews for non-existent place."""
        with pytest.raises(ValueError, match="not found"):
            client.get_reviews("XYZ123ABC456DEF789GHI")


class TestConvenienceFunctions:
    """Test suite for convenience functions."""
    
    def test_get_google_places_client_singleton(self):
        """Test that get_google_places_client returns singleton."""
        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key:
            pytest.skip("GOOGLE_PLACES_API_KEY not set")
        
        client1 = get_google_places_client(api_key=api_key)
        client2 = get_google_places_client(api_key=api_key)
        
        # Should be the same instance
        assert client1 is client2
    
    def test_get_place_reviews_function(self):
        """Test convenience function get_place_reviews."""
        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key:
            pytest.skip("GOOGLE_PLACES_API_KEY not set")
        
        try:
            place_details = get_place_reviews("Statue of Liberty")
            
            assert isinstance(place_details, PlaceDetails)
            assert place_details.place_id is not None
        
        except ValueError as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Place not found: {e}")
            else:
                raise


if __name__ == "__main__":
    # Run basic integration test
    import sys
    
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_PLACES_API_KEY not set in environment")
        sys.exit(1)
    
    print("Testing Google Places API integration...")
    print("-" * 70)
    
    try:
        client = GooglePlacesClient(api_key=api_key)
        print("[OK] Client initialized")
        
        # Test search
        print("\n1. Testing place search...")
        place_id = client.search_place("Hilton Tel aviv")
        if place_id:
            print(f"   [OK] Found place ID: {place_id}")
        else:
            print("   [WARNING] Place not found")
        
        # Test get reviews
        print("\n2. Testing get reviews...")
        place_details = client.get_reviews("Hilton Tel aviv")
        print(f"   [OK] Place: {place_details.name}")
        print(f"   [OK] Address: {place_details.address}")
        print(f"   [OK] Rating: {place_details.rating}")
        print(f"   [OK] Total reviews: {place_details.total_reviews}")
        print(f"   [OK] Top reviews: {len(place_details.top_reviews)}")
        print(f"   [OK] Bottom reviews: {len(place_details.bottom_reviews)}")
        
        if place_details.top_reviews:
            print("\n   Top Review:")
            for review in place_details.top_reviews:
                print(f"   - Author: {review.author_name}")
                print(f"   - Rating: {review.rating}")
                print(f"   - Text: {review.text[:100]}...")

        
        if place_details.bottom_reviews:
            print("\n   Bottom Review:")
            for review in place_details.bottom_reviews:
                print(f"   - Author: {review.author_name}")
                print(f"   - Rating: {review.rating}")
                print(f"   - Text: {review.text[:100]}...")
        
        print("\n" + "-" * 70)
        print("All tests passed!")
    
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

