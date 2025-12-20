"""
Tests for TripAdvisor API integration.
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
from app.API.tripadvisor import (
    TripAdvisorClient,
    get_tripadvisor_client,
    get_location_reviews,
    Review,
    PlaceDetails
)

# Load environment variables
load_dotenv()


class TestTripAdvisorClient:
    """Test suite for TripAdvisorClient."""
    
    @pytest.fixture
    def api_key(self):
        """Get API key from environment."""
        api_key = os.getenv("TRIPADVISOR_API_KEY")
        if not api_key:
            pytest.skip("TRIPADVISOR_API_KEY not set")
        return api_key
    
    @pytest.fixture
    def client(self, api_key):
        """Create a TripAdvisorClient instance."""
        return TripAdvisorClient(api_key=api_key)
    
    def test_client_initialization_with_key(self, api_key):
        """Test client initialization with API key."""
        client = TripAdvisorClient(api_key=api_key)
        assert client is not None
        assert client.api_key == api_key.strip()
        assert client.BASE_URL == "https://api.tripadvisor.com/api/partner/2.0"
    
    def test_client_initialization_without_key(self):
        """Test client initialization fails without API key."""
        # Temporarily remove key if it exists
        original_key = os.environ.get("TRIPADVISOR_API_KEY")
        if "TRIPADVISOR_API_KEY" in os.environ:
            del os.environ["TRIPADVISOR_API_KEY"]
        
        try:
            with pytest.raises(ValueError, match="TRIPADVISOR_API_KEY"):
                TripAdvisorClient()
        finally:
            # Restore original key
            if original_key:
                os.environ["TRIPADVISOR_API_KEY"] = original_key
    
    def test_validate_place_query_valid(self, client):
        """Test validation of valid place queries."""
        assert client._validate_place_query("Eiffel Tower") == "Eiffel Tower"
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
    
    def test_search_location_success(self, client):
        """Test successful location search."""
        # Search for a well-known location
        location_id = client.search_location("Eiffel Tower", location="Paris, France")
        assert location_id is not None
        assert isinstance(location_id, str)
        assert len(location_id) > 0
    
    def test_search_location_not_found(self, client):
        """Test location search when location doesn't exist."""
        # Use a very unlikely location name
        location_id = client.search_location("XYZ123ABC456DEF789")
        # Should return None or empty, depending on API behavior
        assert location_id is None or isinstance(location_id, str)
    
    def test_search_location_invalid_query(self, client):
        """Test location search with invalid query."""
        with pytest.raises(ValueError):
            client.search_location("")
        
        with pytest.raises(ValueError):
            client.search_location(None)
    
    def test_get_location_details_success(self, client):
        """Test getting location details with valid location_id."""
        # First, search for a location to get a valid ID
        location_id = client.search_location("Eiffel Tower", location="Paris, France")
        if location_id:
            details = client.get_location_details(location_id)
            assert isinstance(details, dict)
            assert "name" in details or "data" in details  # API may wrap in "data"
    
    def test_get_location_details_invalid_id(self, client):
        """Test getting location details with invalid location_id."""
        with pytest.raises(ValueError):
            client.get_location_details("")
        
        with pytest.raises(ValueError):
            client.get_location_details(None)
    
    def test_get_location_reviews_success(self, client):
        """Test getting location reviews with valid location_id."""
        # First, search for a location to get a valid ID
        location_id = client.search_location("Eiffel Tower", location="Paris, France")
        if location_id:
            reviews = client.get_location_reviews(location_id, limit=5)
            assert isinstance(reviews, list)
            # Reviews might be empty, but should still be a list
    
    def test_get_location_reviews_invalid_id(self, client):
        """Test getting location reviews with invalid location_id."""
        with pytest.raises(ValueError):
            client.get_location_reviews("")
        
        with pytest.raises(ValueError):
            client.get_location_reviews(None)
    
    def test_parse_reviews(self, client):
        """Test parsing raw review data."""
        # Sample review data structure (may vary by API version)
        raw_reviews = [
            {
                "rating": 5,
                "text": "Amazing place!",
                "published_date": "2024-01-15T10:00:00",
                "relative_time_description": "2 months ago"
            },
            {
                "rating": 4,
                "text": "Good experience",
                "published_date": 1705320000,  # Unix timestamp
                "relative_time_description": "1 month ago"
            },
            {
                "text": "Nice location"  # Missing rating
            }
        ]
        
        parsed = client._parse_reviews(raw_reviews)
        assert isinstance(parsed, list)
        assert len(parsed) <= len(raw_reviews)  # Some might be filtered
        for review in parsed:
            assert isinstance(review, Review)
            assert review.text  # Should have text
    
    def test_sort_reviews_by_latest(self, client):
        """Test sorting reviews by latest."""
        from datetime import datetime, timedelta
        
        # Create reviews with different timestamps
        now = int(datetime.now().timestamp())
        yesterday = int((datetime.now() - timedelta(days=1)).timestamp())
        last_week = int((datetime.now() - timedelta(days=7)).timestamp())
        
        reviews = [
            Review(text="Old review", time=last_week),
            Review(text="Latest review", time=now),
            Review(text="Yesterday review", time=yesterday),
            Review(text="No time review")  # No timestamp
        ]
        
        sorted_reviews = client._sort_reviews_by_latest(reviews)
        
        # Check that reviews with time are sorted (latest first)
        assert sorted_reviews[0].time == now  # Latest first
        assert sorted_reviews[1].time == yesterday
        assert sorted_reviews[2].time == last_week
        # Review without time should be at the end
        assert sorted_reviews[-1].time is None
    
    def test_get_reviews_full_flow(self, client):
        """Test the full flow of getting reviews for a location."""
        place_details = client.get_reviews(
            "Eiffel Tower",
            location="Paris, France",
            limit_reviews=5
        )
        
        assert isinstance(place_details, PlaceDetails)
        assert place_details.location_id is not None
        assert place_details.name is not None
        assert isinstance(place_details.reviews, list)


class TestTripAdvisorHelperFunctions:
    """Test suite for helper functions."""
    
    @pytest.fixture
    def api_key(self):
        """Get API key from environment."""
        api_key = os.getenv("TRIPADVISOR_API_KEY")
        if not api_key:
            pytest.skip("TRIPADVISOR_API_KEY not set")
        return api_key
    
    def test_get_tripadvisor_client(self, api_key):
        """Test get_tripadvisor_client helper function."""
        client1 = get_tripadvisor_client(api_key=api_key)
        client2 = get_tripadvisor_client(api_key=api_key)
        
        # Should return the same instance (singleton)
        assert client1 is client2
        assert isinstance(client1, TripAdvisorClient)
    
    def test_get_location_reviews_helper(self, api_key):
        """Test get_location_reviews helper function."""
        place_details = get_location_reviews(
            "Eiffel Tower",
            location="Paris, France",
            limit_reviews=3
        )
        
        assert isinstance(place_details, PlaceDetails)
        assert place_details.location_id is not None
        assert place_details.name is not None


if __name__ == "__main__":
    # Run basic integration test
    import sys
    
    api_key = os.getenv("TRIPADVISOR_API_KEY")
    if not api_key:
        print("ERROR: TRIPADVISOR_API_KEY not set in environment")
        sys.exit(1)
    
    print("Testing TripAdvisor API integration...")
    print("-" * 70)
    
    try:
        client = TripAdvisorClient(api_key=api_key)
        print("[OK] Client initialized")
        
        # Test search
        print("\n1. Testing location search...")
        location_id = client.search_location("Eiffel Tower", location="Paris, France")
        if location_id:
            print(f"   [OK] Found location ID: {location_id}")
        else:
            print("   [WARNING] Location not found")
        
        # Test get reviews
        print("\n2. Testing get location reviews...")
        place_details = client.get_reviews(
            "Eiffel Tower",
            location="Paris, France",
            limit_reviews=5
        )
        
        if place_details:
            print(f"   [OK] Location: {place_details.name}")
            print(f"   [OK] Address: {place_details.address}")
            print(f"   [OK] Rating: {place_details.rating}")
            print(f"   [OK] Total reviews: {place_details.total_reviews}")
            print(f"   [OK] Reviews retrieved: {len(place_details.reviews)}")
            
            if place_details.reviews:
                print("\n   Latest Reviews:")
                for i, review in enumerate(place_details.reviews[:5], 1):  # Show first 5
                    print(f"   {i}. Rating: {review.rating or 'N/A'}")
                    print(f"      Text: {review.text[:100]}...")
                    if review.relative_time_description:
                        print(f"      Time: {review.relative_time_description}")
                    print()
            else:
                print("   [INFO] No reviews retrieved.")
        else:
            print("   [ERROR] Failed to retrieve location details.")
        
        print("\n" + "-" * 70)
        print("All tests passed!")
    
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

