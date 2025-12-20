"""
Google Places API integration for fetching place reviews.

This module provides functionality to search for places and retrieve
the latest reviews without author names.
"""
import os
import logging
from typing import List, Dict, Optional, Tuple
import googlemaps
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class Review(BaseModel):
    """Represents a review from Google Places."""
    rating: int = Field(ge=1, le=5)
    text: str
    time: Optional[int] = None
    relative_time_description: Optional[str] = None


class PlaceDetails(BaseModel):
    """Represents place details with reviews."""
    place_id: str
    name: str
    address: Optional[str] = None
    rating: Optional[float] = Field(default=None, ge=0, le=5)
    total_reviews: Optional[int] = None
    reviews: List[Review] = Field(default_factory=list)


class GooglePlacesClient:
    """Client for interacting with Google Places API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Google Places client.
        
        Args:
            api_key: Google Places API key (defaults to GOOGLE_PLACES_API_KEY env var)
        
        Raises:
            ValueError: If API key is not provided
        """
        api_key = api_key or os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_PLACES_API_KEY environment variable is not set")
        
        self.client = googlemaps.Client(key=api_key)
        logger.info("Google Places client initialized")
    
    def _validate_place_query(self, query: str) -> str:
        """
        Validate and sanitize place query.
        
        Args:
            query: The place name or query string
        
        Returns:
            Sanitized query string
        
        Raises:
            ValueError: If query is invalid
        """
        if not query or not isinstance(query, str):
            raise ValueError("Place query must be a non-empty string")
        
        query = query.strip()
        if len(query) < 2:
            raise ValueError("Place query must be at least 2 characters long")
        
        if len(query) > 200:
            raise ValueError("Place query must be less than 200 characters")
        
        return query
    
    def search_place(self, query: str) -> Optional[str]:
        """
        Search for a place by name and return its place_id.
        
        Args:
            query: The place name or query string (e.g., "Starbucks New York")
        
        Returns:
            Place ID if found, None otherwise
        
        Raises:
            ValueError: If query is invalid
            Exception: If API call fails
        """
        query = self._validate_place_query(query)
        
        try:
            logger.info(f"Searching for place: {query}")
            places_result = self.client.places(query=query)
            
            if not places_result.get("results"):
                logger.warning(f"No places found for query: {query}")
                return None
            
            place_id = places_result["results"][0]["place_id"]
            place_name = places_result["results"][0].get("name", "Unknown")
            logger.info(f"Found place: {place_name} (ID: {place_id})")
            return place_id
        
        except googlemaps.exceptions.ApiError as e:
            logger.error(f"Google Places API error: {e}")
            raise Exception(f"Failed to search place: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error searching place: {e}")
            raise
    
    def get_place_details(self, place_id: str, fields: Optional[List[str]] = None) -> Dict:
        """
        Get detailed information about a place.
        
        Args:
            place_id: The Google Places place ID
            fields: Optional list of fields to retrieve (defaults to common fields)
        
        Returns:
            Dictionary containing place details
        
        Raises:
            ValueError: If place_id is invalid
            Exception: If API call fails
        """
        if not place_id or not isinstance(place_id, str):
            raise ValueError("place_id must be a non-empty string")
        
        if fields is None:
            fields = [
                "place_id",
                "name",
                "formatted_address",
                "rating",
                "user_ratings_total",
                "reviews"
            ]
        
        try:
            logger.info(f"Fetching details for place_id: {place_id}")
            place_details = self.client.place(
                place_id=place_id,
                fields=fields
            )
            
            if "result" not in place_details:
                logger.warning(f"No details found for place_id: {place_id}")
                return {}
            
            return place_details["result"]
        
        except googlemaps.exceptions.ApiError as e:
            logger.error(f"Google Places API error: {e}")
            raise Exception(f"Failed to get place details: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error getting place details: {e}")
            raise
    
    def _parse_reviews(self, reviews: List[Dict]) -> List[Review]:
        """
        Parse raw review data into Review objects (without author names).
        
        Args:
            reviews: List of raw review dictionaries from API
        
        Returns:
            List of Review objects (rating and text only)
        """
        parsed_reviews = []
        
        for review_data in reviews:
            try:
                review = Review(
                    rating=review_data.get("rating", 0),
                    text=review_data.get("text", ""),
                    time=review_data.get("time"),
                    relative_time_description=review_data.get("relative_time_description")
                )
                parsed_reviews.append(review)
            except Exception as e:
                logger.warning(f"Failed to parse review: {e}")
                continue
        
        return parsed_reviews
    
    def _sort_reviews_by_latest(
        self,
        reviews: List[Review]
    ) -> List[Review]:
        """
        Sort reviews by time (latest first).
        
        Args:
            reviews: List of Review objects
        
        Returns:
            List of reviews sorted by time (latest first)
        """
        if not reviews:
            return []
        
        # Sort by time descending (latest first)
        # Reviews without time will be placed at the end
        sorted_reviews = sorted(
            reviews,
            key=lambda r: r.time if r.time is not None else 0,
            reverse=True
        )
        
        return sorted_reviews
    
    def get_reviews(
        self,
        query: str
    ) -> PlaceDetails:
        """
        Get place reviews - latest reviews sorted by time.
        
        This function searches for a place, retrieves its details and reviews,
        then returns the latest reviews (sorted by time) without author names.
        
        Args:
            query: Place name or query string (e.g., "Central Park New York")
        
        Returns:
            PlaceDetails object containing place info and latest reviews
        
        Raises:
            ValueError: If query is invalid or place not found
            Exception: If API call fails
        """
        # Search for place
        place_id = self.search_place(query)
        if not place_id:
            raise ValueError(f"Place not found for query: {query}")
        
        # Get place details with reviews
        place_data = self.get_place_details(place_id)
        
        if not place_data:
            raise ValueError(f"Could not retrieve details for place: {query}")
        
        # Parse reviews
        raw_reviews = place_data.get("reviews", [])
        if not raw_reviews:
            logger.warning(f"No reviews found for place: {query}")
        
        reviews = self._parse_reviews(raw_reviews)
        
        # Sort by latest (time)
        sorted_reviews = self._sort_reviews_by_latest(reviews)
        
        # Build result
        place_details = PlaceDetails(
            place_id=place_id,
            name=place_data.get("name", "Unknown"),
            address=place_data.get("formatted_address"),
            rating=place_data.get("rating"),
            total_reviews=place_data.get("user_ratings_total"),
            reviews=sorted_reviews
        )
        
        logger.info(
            f"Retrieved {len(sorted_reviews)} reviews for {place_details.name} "
            f"(sorted by latest)"
        )
        
        return place_details


# Global client instance (initialized on first use)
_places_client: Optional[GooglePlacesClient] = None


def get_google_places_client(api_key: Optional[str] = None) -> GooglePlacesClient:
    """
    Get or create a Google Places client instance.
    
    Args:
        api_key: Optional API key (uses env var if not provided)
    
    Returns:
        GooglePlacesClient instance
    """
    global _places_client
    
    if _places_client is None:
        _places_client = GooglePlacesClient(api_key=api_key)
    
    return _places_client


def get_place_reviews(query: str) -> PlaceDetails:
    """
    Convenience function to get place reviews.
    
    Args:
        query: Place name or query string
    
    Returns:
        PlaceDetails object with latest reviews (sorted by time)
    """
    client = get_google_places_client()
    return client.get_reviews(query)

