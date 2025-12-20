"""
Tests for Yelp API integration.
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
from app.API.yelp import (
    YelpClient,
    get_yelp_client,
    get_business_reviews,
    Review,
    BusinessDetails
)

# Load environment variables
load_dotenv()


class TestYelpClient:
    """Test suite for YelpClient."""
    
    @pytest.fixture
    def api_key(self):
        """Get API key from environment."""
        api_key = os.getenv("YELP_API_KEY")
        if not api_key:
            pytest.skip("YELP_API_KEY not set")
        return api_key
    
    @pytest.fixture
    def client(self, api_key):
        """Create a YelpClient instance."""
        return YelpClient(api_key=api_key)
    
    def test_client_initialization_with_key(self, api_key):
        """Test client initialization with API key."""
        client = YelpClient(api_key=api_key)
        assert client is not None
        assert client.api_key == api_key
        assert "Authorization" in client.headers
        assert f"Bearer {api_key}" in client.headers["Authorization"]
    
    def test_client_initialization_without_key(self):
        """Test client initialization fails without API key."""
        # Temporarily remove key if it exists
        original_key = os.environ.get("YELP_API_KEY")
        if "YELP_API_KEY" in os.environ:
            del os.environ["YELP_API_KEY"]
        
        try:
            with pytest.raises(ValueError, match="YELP_API_KEY"):
                YelpClient()
        finally:
            # Restore original key
            if original_key:
                os.environ["YELP_API_KEY"] = original_key
    
    def test_validate_business_query_valid(self, client):
        """Test validation of valid business queries."""
        assert client._validate_business_query("Starbucks") == "Starbucks"
        assert client._validate_business_query("  Pizza Place  ") == "Pizza Place"
        assert client._validate_business_query("Coffee Shop") == "Coffee Shop"
    
    def test_validate_business_query_invalid(self, client):
        """Test validation rejects invalid business queries."""
        with pytest.raises(ValueError):
            client._validate_business_query("")
        
        with pytest.raises(ValueError):
            client._validate_business_query("a")
        
        with pytest.raises(ValueError):
            client._validate_business_query(None)
        
        with pytest.raises(ValueError):
            client._validate_business_query("a" * 201)  # Too long
    
    def test_search_business_success(self, client):
        """Test successful business search."""
        # Search for a well-known business
        business_id = client.search_business("Starbucks", location="New York, NY")
        assert business_id is not None
        assert isinstance(business_id, str)
        assert len(business_id) > 0
    
    def test_search_business_without_location(self, client):
        """Test business search without location."""
        # Some queries work without location, others don't
        try:
            business_id = client.search_business("Starbucks")
            # Should either find something or return None
            assert business_id is None or isinstance(business_id, str)
        except Exception:
            # Some API configurations require location
            pytest.skip("Business search requires location for this API configuration")
    
    def test_search_business_not_found(self, client):
        """Test business search when business doesn't exist."""
        # Use a very unlikely business name
        business_id = client.search_business("XYZ123ABC456DEF789", location="New York, NY")
        # Should return None or empty, depending on API behavior
        assert business_id is None or isinstance(business_id, str)
    
    def test_search_business_invalid_query(self, client):
        """Test business search with invalid query."""
        with pytest.raises(ValueError):
            client.search_business("")
        
        with pytest.raises(ValueError):
            client.search_business("a")
    
    def test_get_business_details_success(self, client):
        """Test getting business details."""
        # First search for a business
        business_id = client.search_business("Starbucks", location="Times Square, New York, NY")
        if not business_id:
            pytest.skip("Could not find business for testing")
        
        details = client.get_business_details(business_id)
        assert isinstance(details, dict)
        assert "id" in details or "name" in details
    
    def test_get_business_details_invalid_id(self, client):
        """Test getting details with invalid business_id."""
        with pytest.raises(ValueError):
            client.get_business_details("")
        
        with pytest.raises(ValueError):
            client.get_business_details(None)
    
    def test_parse_reviews_valid(self, client):
        """Test parsing valid review data."""
        raw_reviews = [
            {
                "user": {"name": "John Doe"},
                "rating": 5,
                "text": "Great place!",
                "time_created": "2024-01-15 10:00:00",
                "url": "https://yelp.com/review/123"
            },
            {
                "user": {"name": "Jane Smith"},
                "rating": 3,
                "text": "Okay place.",
                "time_created": "2024-01-14 10:00:00"
            }
        ]
        
        reviews = client._parse_reviews(raw_reviews)
        assert len(reviews) == 2
        assert all(isinstance(r, Review) for r in reviews)
        assert reviews[0].user_name == "John Doe"
        assert reviews[0].rating == 5
        assert reviews[1].rating == 3
    
    def test_sort_and_split_reviews(self, client):
        """Test sorting and splitting reviews into top/bottom."""
        reviews = [
            Review(user_name="User1", rating=5, text="Great"),
            Review(user_name="User2", rating=1, text="Bad"),
            Review(user_name="User3", rating=4, text="Good"),
            Review(user_name="User4", rating=2, text="Poor"),
            Review(user_name="User5", rating=5, text="Excellent"),
            Review(user_name="User6", rating=3, text="Average"),
            Review(user_name="User7", rating=1, text="Terrible"),
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
        # Test with a well-known business
        try:
            business_details = client.get_reviews(
                "Starbucks",
                location="Times Square, New York, NY"
            )
            
            assert isinstance(business_details, BusinessDetails)
            assert business_details.business_id is not None
            assert business_details.name is not None
            
            # Should have top and bottom reviews (may be empty if reviews not available)
            assert isinstance(business_details.top_reviews, list)
            assert isinstance(business_details.bottom_reviews, list)
            assert len(business_details.top_reviews) <= 5
            assert len(business_details.bottom_reviews) <= 5
        
        except ValueError as e:
            # Business not found is acceptable
            if "not found" in str(e).lower():
                pytest.skip(f"Business not found: {e}")
            else:
                raise
    
    def test_get_reviews_business_not_found(self, client):
        """Test getting reviews for non-existent business."""
        with pytest.raises(ValueError, match="not found"):
            client.get_reviews(
                "XYZ123ABC456DEF789GHI",
                location="New York, NY"
            )


class TestConvenienceFunctions:
    """Test suite for convenience functions."""
    
    def test_get_yelp_client_singleton(self):
        """Test that get_yelp_client returns singleton."""
        api_key = os.getenv("YELP_API_KEY")
        if not api_key:
            pytest.skip("YELP_API_KEY not set")
        
        client1 = get_yelp_client(api_key=api_key)
        client2 = get_yelp_client(api_key=api_key)
        
        # Should be the same instance
        assert client1 is client2
    
    def test_get_business_reviews_function(self):
        """Test convenience function get_business_reviews."""
        api_key = os.getenv("YELP_API_KEY")
        if not api_key:
            pytest.skip("YELP_API_KEY not set")
        
        try:
            business_details = get_business_reviews(
                "Starbucks",
                location="New York, NY"
            )
            
            assert isinstance(business_details, BusinessDetails)
            assert business_details.business_id is not None
        
        except ValueError as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Business not found: {e}")
            else:
                raise


if __name__ == "__main__":
    # Run basic integration test
    import sys
    
    api_key = os.getenv("YELP_API_KEY")
    if not api_key:
        print("ERROR: YELP_API_KEY not set in environment")
        sys.exit(1)
    
    print("Testing Yelp API integration...")
    print("-" * 70)
    
    try:
        client = YelpClient(api_key=api_key)
        print("[OK] Client initialized")
        
        # Test search
        print("\n1. Testing business search...")
        business_id = client.search_business("Starbucks", location="Times Square, New York, NY")
        if business_id:
            print(f"   [OK] Found business ID: {business_id}")
        else:
            print("   [WARNING] Business not found")
        
        # Test get reviews
        print("\n2. Testing get reviews...")
        business_details = client.get_reviews(
            "Starbucks",
            location="Times Square, New York, NY"
        )
        print(f"   [OK] Business: {business_details.name}")
        print(f"   [OK] Address: {business_details.address}")
        print(f"   [OK] Rating: {business_details.rating}")
        print(f"   [OK] Total reviews: {business_details.total_reviews}")
        print(f"   [OK] Top reviews: {len(business_details.top_reviews)}")
        print(f"   [OK] Bottom reviews: {len(business_details.bottom_reviews)}")
        
        if business_details.top_reviews:
            print("\n   Top Review:")
            top_review = business_details.top_reviews[0]
            print(f"   - User: {top_review.user_name}")
            print(f"   - Rating: {top_review.rating}")
            print(f"   - Text: {top_review.text[:100]}...")
        else:
            print("\n   [NOTE] No reviews available via API")
            print("   (Yelp Fusion API may require Reviews API endpoint)")
        
        print("\n" + "-" * 70)
        print("All tests passed!")
    
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

