"""
Yelp Fusion API integration for fetching business reviews.

This module provides functionality to search for businesses and retrieve
the top 5 highest-rated reviews and bottom 5 lowest-rated reviews.
"""
import os
import logging
from typing import List, Dict, Optional, Tuple
import requests
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Review(BaseModel):
    """Represents a review from Yelp."""
    user_name: str
    rating: int = Field(ge=1, le=5)
    text: str
    time_created: Optional[str] = None
    url: Optional[str] = None


class BusinessDetails(BaseModel):
    """Represents business details with reviews."""
    business_id: str
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    rating: Optional[float] = Field(default=None, ge=0, le=5)
    total_reviews: Optional[int] = None
    top_reviews: List[Review] = Field(default_factory=list)
    bottom_reviews: List[Review] = Field(default_factory=list)


class YelpClient:
    """Client for interacting with Yelp Fusion API."""
    
    BASE_URL = "https://api.yelp.com/v3"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Yelp client.
        
        Args:
            api_key: Yelp Fusion API key (defaults to YELP_API_KEY env var)
        
        Raises:
            ValueError: If API key is not provided
        """
        api_key = api_key or os.getenv("YELP_API_KEY")
        if not api_key:
            raise ValueError("YELP_API_KEY environment variable is not set")
        
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        logger.info("Yelp client initialized")
    
    def _validate_business_query(self, query: str) -> str:
        """
        Validate and sanitize business query.
        
        Args:
            query: The business name or query string
        
        Returns:
            Sanitized query string
        
        Raises:
            ValueError: If query is invalid
        """
        if not query or not isinstance(query, str):
            raise ValueError("Business query must be a non-empty string")
        
        query = query.strip()
        if len(query) < 2:
            raise ValueError("Business query must be at least 2 characters long")
        
        if len(query) > 200:
            raise ValueError("Business query must be less than 200 characters")
        
        return query
    
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None
    ) -> Dict:
        """
        Make an API request to Yelp.
        
        Args:
            endpoint: API endpoint (relative to BASE_URL)
            params: Optional query parameters
        
        Returns:
            JSON response as dictionary
        
        Raises:
            Exception: If API call fails
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"Yelp API HTTP error: {e}")
            if response.status_code == 401:
                raise Exception("Invalid Yelp API key")
            elif response.status_code == 404:
                raise Exception(f"Resource not found: {endpoint}")
            else:
                raise Exception(f"Yelp API error: {str(e)}")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Yelp API request error: {e}")
            raise Exception(f"Failed to connect to Yelp API: {str(e)}")
    
    def search_business(
        self,
        query: str,
        location: Optional[str] = None,
        limit: int = 1
    ) -> Optional[str]:
        """
        Search for a business by name and return its business_id.
        
        Args:
            query: The business name or query string (e.g., "Starbucks")
            location: Optional location (e.g., "New York, NY")
            limit: Maximum number of results (default: 1)
        
        Returns:
            Business ID if found, None otherwise
        
        Raises:
            ValueError: If query is invalid
            Exception: If API call fails
        """
        query = self._validate_business_query(query)
        
        try:
            logger.info(f"Searching for business: {query}")
            
            params = {
                "term": query,
                "limit": limit
            }
            
            if location:
                params["location"] = location.strip()
            
            response = self._make_request("/businesses/search", params=params)
            
            businesses = response.get("businesses", [])
            if not businesses:
                logger.warning(f"No businesses found for query: {query}")
                return None
            
            business_id = businesses[0]["id"]
            business_name = businesses[0].get("name", "Unknown")
            logger.info(f"Found business: {business_name} (ID: {business_id})")
            return business_id
        
        except Exception as e:
            logger.error(f"Error searching business: {e}")
            raise
    
    def get_business_details(self, business_id: str) -> Dict:
        """
        Get detailed information about a business including reviews.
        
        Args:
            business_id: The Yelp business ID
        
        Returns:
            Dictionary containing business details
        
        Raises:
            ValueError: If business_id is invalid
            Exception: If API call fails
        """
        if not business_id or not isinstance(business_id, str):
            raise ValueError("business_id must be a non-empty string")
        
        try:
            logger.info(f"Fetching details for business_id: {business_id}")
            business_data = self._make_request(f"/businesses/{business_id}")
            
            if not business_data:
                logger.warning(f"No details found for business_id: {business_id}")
                return {}
            
            return business_data
        
        except Exception as e:
            logger.error(f"Error getting business details: {e}")
            raise
    
    def get_business_reviews(self, business_id: str) -> List[Dict]:
        """
        Get reviews for a business.
        
        IMPORTANT NOTE: The Yelp Fusion API v3 business endpoint does NOT include
        reviews. To get reviews, you need to use the Yelp Reviews API (separate endpoint)
        or upgrade to a Yelp API plan that includes reviews.
        
        This implementation checks if reviews are available in the business details
        (which is unlikely), and returns an empty list if not found.
        
        To get actual reviews, you would need to:
        1. Use the Yelp Reviews API endpoint (if available in your plan)
        2. Or integrate with Yelp's Reviews API separately
        
        Args:
            business_id: The Yelp business ID
        
        Returns:
            List of review dictionaries (likely empty)
        
        Raises:
            ValueError: If business_id is invalid
            Exception: If API call fails
        """
        if not business_id or not isinstance(business_id, str):
            raise ValueError("business_id must be a non-empty string")
        
        try:
            # Try to get reviews from the Reviews API endpoint
            # Note: This endpoint may not be available in all Yelp API plans
            try:
                reviews_data = self._make_request(f"/businesses/{business_id}/reviews")
                reviews = reviews_data.get("reviews", [])
                
                if reviews:
                    logger.info(f"Retrieved {len(reviews)} reviews from Reviews API")
                    return reviews
            except Exception as e:
                logger.debug(f"Reviews API endpoint not available: {e}")
            
            # Fallback: Check if reviews are in business details (unlikely)
            business_data = self.get_business_details(business_id)
            reviews = business_data.get("reviews", [])
            
            if not reviews:
                logger.info(
                    f"Reviews not available for business {business_id}. "
                    "Yelp Fusion API v3 may require Reviews API endpoint access. "
                    "Check your Yelp API plan."
                )
            
            return reviews
        
        except Exception as e:
            logger.error(f"Error getting business reviews: {e}")
            raise
    
    def _parse_reviews(self, reviews: List[Dict]) -> List[Review]:
        """
        Parse raw review data into Review objects.
        
        Args:
            reviews: List of raw review dictionaries from API
        
        Returns:
            List of Review objects
        """
        parsed_reviews = []
        
        for review_data in reviews:
            try:
                review = Review(
                    user_name=review_data.get("user", {}).get("name", "Anonymous"),
                    rating=review_data.get("rating", 0),
                    text=review_data.get("text", ""),
                    time_created=review_data.get("time_created"),
                    url=review_data.get("url")
                )
                parsed_reviews.append(review)
            except Exception as e:
                logger.warning(f"Failed to parse review: {e}")
                continue
        
        return parsed_reviews
    
    def _sort_and_split_reviews(
        self,
        reviews: List[Review]
    ) -> Tuple[List[Review], List[Review]]:
        """
        Sort reviews by rating and return top 5 and bottom 5.
        
        Args:
            reviews: List of Review objects
        
        Returns:
            Tuple of (top_reviews, bottom_reviews)
        """
        if not reviews:
            return [], []
        
        # Sort by rating descending (highest first)
        sorted_reviews = sorted(reviews, key=lambda r: r.rating, reverse=True)
        
        # Get top 5 highest rated
        top_reviews = sorted_reviews[:5]
        
        # Get bottom 5 lowest rated (reverse sorted list, take last 5, reverse back)
        bottom_reviews = sorted_reviews[-5:]
        bottom_reviews.reverse()  # Show lowest first
        
        return top_reviews, bottom_reviews
    
    def get_reviews(
        self,
        query: str,
        location: Optional[str] = None
    ) -> BusinessDetails:
        """
        Get business reviews - top 5 and bottom 5.
        
        This function searches for a business, retrieves its details and reviews,
        then returns the top 5 highest-rated and bottom 5 lowest-rated reviews.
        
        Args:
            query: Business name or query string (e.g., "Starbucks")
            location: Optional location to narrow search (e.g., "New York, NY")
        
        Returns:
            BusinessDetails object containing business info and sorted reviews
        
        Raises:
            ValueError: If query is invalid or business not found
            Exception: If API call fails
        """
        # Search for business
        business_id = self.search_business(query, location=location)
        if not business_id:
            raise ValueError(f"Business not found for query: {query}")
        
        # Get business details
        business_data = self.get_business_details(business_id)
        
        if not business_data:
            raise ValueError(f"Could not retrieve details for business: {query}")
        
        # Get reviews
        raw_reviews = self.get_business_reviews(business_id)
        
        if not raw_reviews:
            logger.warning(f"No reviews found for business: {query}")
        
        reviews = self._parse_reviews(raw_reviews)
        
        # Sort and split into top/bottom
        top_reviews, bottom_reviews = self._sort_and_split_reviews(reviews)
        
        # Extract address components
        location_data = business_data.get("location", {})
        address_parts = location_data.get("display_address", [])
        full_address = ", ".join(address_parts) if address_parts else None
        
        # Build result
        business_details = BusinessDetails(
            business_id=business_id,
            name=business_data.get("name", "Unknown"),
            address=full_address,
            city=location_data.get("city"),
            state=location_data.get("state"),
            zip_code=location_data.get("zip_code"),
            rating=business_data.get("rating"),
            total_reviews=business_data.get("review_count"),
            top_reviews=top_reviews,
            bottom_reviews=bottom_reviews
        )
        
        logger.info(
            f"Retrieved reviews for {business_details.name}: "
            f"{len(top_reviews)} top, {len(bottom_reviews)} bottom"
        )
        
        return business_details


# Global client instance (initialized on first use)
_yelp_client: Optional[YelpClient] = None


def get_yelp_client(api_key: Optional[str] = None) -> YelpClient:
    """
    Get or create a Yelp client instance.
    
    Args:
        api_key: Optional API key (uses env var if not provided)
    
    Returns:
        YelpClient instance
    """
    global _yelp_client
    
    if _yelp_client is None:
        _yelp_client = YelpClient(api_key=api_key)
    
    return _yelp_client


def get_business_reviews(
    query: str,
    location: Optional[str] = None
) -> BusinessDetails:
    """
    Convenience function to get business reviews.
    
    Args:
        query: Business name or query string
        location: Optional location to narrow search
    
    Returns:
        BusinessDetails object with top 5 and bottom 5 reviews
    """
    client = get_yelp_client()
    return client.get_reviews(query, location=location)

