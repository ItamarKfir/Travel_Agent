"""
TripAdvisor API integration for fetching place reviews.

This module provides functionality to search for places and retrieve
the latest reviews without author names.
"""
import os
import logging
from typing import List, Dict, Optional
import requests
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Review(BaseModel):
    """Represents a review from TripAdvisor."""
    rating: Optional[float] = Field(default=None, ge=1, le=5)
    text: str
    time: Optional[int] = None  # Unix timestamp
    relative_time_description: Optional[str] = None


class PlaceDetails(BaseModel):
    """Represents place details with reviews."""
    location_id: str
    name: str
    address: Optional[str] = None
    rating: Optional[float] = Field(default=None, ge=0, le=5)
    total_reviews: Optional[int] = None
    reviews: List[Review] = Field(default_factory=list)


class TripAdvisorClient:
    """Client for interacting with TripAdvisor API."""
    
    BASE_URL = "https://api.content.tripadvisor.com/api/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize TripAdvisor client.
        
        Args:
            api_key: TripAdvisor API key (defaults to TRIPADVISOR_API_KEY env var)
        
        Raises:
            ValueError: If API key is not provided
        """
        api_key = api_key or os.getenv("TRIPADVISOR_API_KEY")
        if not api_key:
            raise ValueError("TRIPADVISOR_API_KEY environment variable is not set")
        
        self.api_key = api_key.strip()
        self.session = requests.Session()
        # TripAdvisor Content API requires User-Agent header
        self.session.headers.update({
            "User-Agent": "Travel-Agent/1.0",
            "Accept": "application/json"
        })
        logger.info("TripAdvisor client initialized")
    
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
    
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None
    ) -> Dict:
        """
        Make an authenticated request to the TripAdvisor API.
        
        Args:
            endpoint: API endpoint (relative to BASE_URL)
            params: Optional query parameters
        
        Returns:
            JSON response as dictionary
        
        Raises:
            Exception: If API call fails
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        # Add API key to params
        request_params = {"key": self.api_key}
        if params:
            request_params.update(params)
        
        try:
            logger.debug(f"Making request to: {url} with params: {request_params}")
            response = self.session.get(url, params=request_params, timeout=10)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            error_message = str(e)
            try:
                error_data = response.json()
                error_message = error_data.get("error", {}).get("message", str(e))
                logger.error(f"API Error Response: {error_data}")
            except:
                try:
                    error_text = response.text
                    logger.error(f"API Error Response (text): {error_text}")
                except:
                    pass
            
            logger.error(f"TripAdvisor API HTTP error: {e}")
            
            if response.status_code == 401:
                raise Exception(
                    f"Invalid TripAdvisor API key or authentication failed (401). "
                    f"Error: {error_message}. "
                    f"Please verify your API key is correct and active."
                )
            elif response.status_code == 404:
                # 404 might mean location not found (business logic) or endpoint not found
                # Check if it's a "location not found" vs actual endpoint error
                if "location was not found" in error_message.lower() or "not found" in error_message.lower():
                    # This is a business logic error (location not found), not an endpoint error
                    logger.warning(f"Location not found: {error_message}")
                    return {}  # Return empty dict to indicate no results
                else:
                    raise Exception(f"Resource not found: {endpoint}. Error: {error_message}")
            else:
                raise Exception(f"TripAdvisor API error: {error_message}")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"TripAdvisor API request error: {e}")
            raise Exception(f"Failed to connect to TripAdvisor API: {str(e)}")
    
    def search_location(
        self,
        query: str,
        location: Optional[str] = None,
        limit: int = 1
    ) -> Optional[str]:
        """
        Search for a location by name and return location data.
        
        Args:
            query: The location name or query string (e.g., "Eiffel Tower Paris")
            location: Optional location to narrow search (e.g., "Paris, France")
            limit: Maximum number of results (default: 1)
        
        Returns:
            Dictionary with location data (including locationId) if found, None otherwise
        
        Raises:
            ValueError: If query is invalid
            Exception: If API call fails
        """
        query = self._validate_place_query(query)
        
        try:
            logger.info(f"Searching for location: {query}")
            
            params = {
                "searchQuery": query,  # TripAdvisor Content API v1 uses 'searchQuery'
                "limit": limit
            }
            
            # TripAdvisor API uses 'near' for location, or latlong for coordinates
            if location:
                # Check if location looks like coordinates (lat,lng)
                if "," in location and any(c.isdigit() for c in location.split(",")[0]):
                    params["latlong"] = location  # Use latlong for coordinates
                else:
                    params["near"] = location  # Use near for location string
            
            response = self._make_request("/location/search", params=params)
            
            # Handle empty response (location not found case)
            if not response or response == {}:
                logger.warning(f"No locations found for query: {query}")
                return None
            
            results = response.get("data", [])
            if not results:
                logger.warning(f"No locations found for query: {query}")
                return None
            
            # Return the full location data from search results
            location_data = results[0]
            location_id = location_data.get("locationId") or location_data.get("location_id")
            location_name = location_data.get("name", "Unknown")
            logger.info(f"Found location: {location_name} (ID: {location_id})")
            return location_data
        
        except Exception as e:
            logger.error(f"Error searching location: {e}")
            raise
    
    def get_location_details(self, location_id: str) -> Dict:
        """
        Get detailed information about a location.
        
        Args:
            location_id: The TripAdvisor location ID
        
        Returns:
            Dictionary containing location details
        
        Raises:
            ValueError: If location_id is invalid
            Exception: If API call fails
        """
        if not location_id or not isinstance(location_id, str):
            raise ValueError("location_id must be a non-empty string")
        
        try:
            logger.info(f"Fetching details for location_id: {location_id}")
            location_data = self._make_request(f"/location/{location_id}")
            
            if not location_data:
                logger.warning(f"No details found for location_id: {location_id}")
                return {}
            
            return location_data.get("data", {})
        
        except Exception as e:
            logger.error(f"Error getting location details: {e}")
            raise
    
    def get_location_reviews(
        self,
        location_id: str,
        limit: int = 5,
        language: str = "en"
    ) -> List[Dict]:
        """
        Get reviews for a location.
        
        Args:
            location_id: The TripAdvisor location ID
            limit: Maximum number of reviews to retrieve (default: 10, max: 100)
        
        Returns:
            List of review dictionaries
        
        Raises:
            ValueError: If location_id is invalid
            Exception: If API call fails
        """
        if not location_id or not isinstance(location_id, str):
            raise ValueError("location_id must be a non-empty string")
        
        try:
            logger.info(f"Fetching reviews for location_id: {location_id}")
            
            # TripAdvisor Content API v1 limits reviews to 5 for most accounts
            params = {
                "limit": min(limit, 5),  # API limit is 5 for most accounts
                "language": language
            }
            
            response = self._make_request(f"/location/{location_id}/reviews", params=params)
            
            # TripAdvisor Content API v1 returns reviews in "data" field as a list
            reviews = response.get("data", [])
            if not isinstance(reviews, list):
                reviews = []
            
            if not reviews:
                logger.info(f"No reviews found for location {location_id}")
            
            return reviews
        
        except Exception as e:
            logger.error(f"Error getting location reviews: {e}")
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
                # TripAdvisor API may return ratings in different formats
                rating = None
                if "rating" in review_data:
                    rating = float(review_data["rating"])
                elif "rating_bubble" in review_data:
                    # Some APIs return rating as "5.0 of 5 bubbles"
                    rating_str = str(review_data["rating_bubble"]).split()[0]
                    try:
                        rating = float(rating_str)
                    except ValueError:
                        pass
                
                # Get review text
                text = (
                    review_data.get("text", "") or
                    review_data.get("review_text", "") or
                    review_data.get("review", "") or
                    ""
                )
                
                # Get timestamp
                time_stamp = None
                if "published_date" in review_data:
                    # Parse published_date if it's a timestamp or ISO string
                    pub_date = review_data["published_date"]
                    if isinstance(pub_date, (int, float)):
                        time_stamp = int(pub_date)
                    elif isinstance(pub_date, str):
                        # Try to parse ISO format or other date formats
                        try:
                            from datetime import datetime
                            # Try common ISO formats
                            for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S"]:
                                try:
                                    dt = datetime.strptime(pub_date.split(".")[0], fmt)
                                    time_stamp = int(dt.timestamp())
                                    break
                                except ValueError:
                                    continue
                        except:
                            pass
                
                # Get relative time description
                relative_time = (
                    review_data.get("relative_time_description") or
                    review_data.get("published_date_string") or
                    None
                )
                
                if text:  # Only add reviews with text
                    review = Review(
                        rating=rating,
                        text=text,
                        time=time_stamp,
                        relative_time_description=relative_time
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
        
        # Separate reviews with and without time
        reviews_with_time = [r for r in reviews if r.time is not None]
        reviews_without_time = [r for r in reviews if r.time is None]
        
        # Sort reviews with time by time descending (latest first)
        sorted_reviews_with_time = sorted(
            reviews_with_time,
            key=lambda r: r.time,
            reverse=True
        )
        
        # Combine sorted reviews with time and reviews without time
        return sorted_reviews_with_time + reviews_without_time
    
    def get_reviews(
        self,
        query: str,
        location: Optional[str] = None,
        limit_reviews: int = 5,
        language: str = "en"
    ) -> PlaceDetails:
        """
        Get location reviews - latest reviews sorted by time.
        
        This function searches for a location, retrieves its details and reviews,
        then returns the latest reviews (sorted by time) without author names.
        
        Args:
            query: Location name or query string (e.g., "Eiffel Tower")
            location: Optional location to narrow search (e.g., "Paris, France")
            limit_reviews: Maximum number of reviews to retrieve (default: 5, max: 5 for most accounts)
            language: Language code for reviews (default: "en")
        
        Returns:
            PlaceDetails object containing location info and latest reviews
        
        Raises:
            ValueError: If query is invalid or location not found
            Exception: If API call fails
        """
        # Search for location (returns full location data, not just ID)
        location_data = self.search_location(query, location=location)
        if not location_data:
            raise ValueError(f"Location not found for query: {query}")
        
        # Extract location_id from location data
        location_id = str(location_data.get("locationId") or location_data.get("location_id") or "")
        if not location_id:
            raise ValueError(f"Location ID not found in search results for query: {query}")
        
        # Get reviews
        raw_reviews = []
        try:
            raw_reviews = self.get_location_reviews(location_id, limit=limit_reviews, language=language)
            if not raw_reviews:
                logger.warning(f"No reviews found for location: {query}")
        except Exception as e:
            # Log error but continue - we still want to return location details
            logger.warning(f"Could not fetch reviews for location {query}: {e}")
            raw_reviews = []
        
        # Parse reviews
        reviews = self._parse_reviews(raw_reviews)
        
        # Sort by latest (time)
        sorted_reviews = self._sort_reviews_by_latest(reviews)
        
        # Extract address
        address = (
            location_data.get("address") or
            location_data.get("address_string") or
            location_data.get("location_string") or
            None
        )
        
        # Extract rating
        rating = None
        if "rating" in location_data:
            try:
                rating = float(location_data["rating"])
            except (ValueError, TypeError):
                pass
        
        # Extract total reviews count
        total_reviews = (
            location_data.get("num_reviews") or
            location_data.get("review_count") or
            location_data.get("total_reviews") or
            None
        )
        
        # Build result
        place_details = PlaceDetails(
            location_id=location_id,
            name=location_data.get("name", "Unknown"),
            address=address,
            rating=rating,
            total_reviews=total_reviews,
            reviews=sorted_reviews
        )
        
        logger.info(
            f"Retrieved {len(sorted_reviews)} latest reviews for {place_details.name}"
        )
        
        return place_details


# Global client instance (initialized on first use)
_tripadvisor_client: Optional[TripAdvisorClient] = None


def get_tripadvisor_client(api_key: Optional[str] = None) -> TripAdvisorClient:
    """
    Get or create a TripAdvisor client instance.
    
    Args:
        api_key: Optional API key (uses env var if not provided)
    
    Returns:
        TripAdvisorClient instance
    """
    global _tripadvisor_client
    
    if _tripadvisor_client is None:
        _tripadvisor_client = TripAdvisorClient(api_key=api_key)
    
    return _tripadvisor_client


def get_location_reviews(
    query: str,
    location: Optional[str] = None,
    limit_reviews: int = 5,
    language: str = "en"
) -> PlaceDetails:
    """
    Convenience function to get location reviews.
    
    Args:
        query: Location name or query string
        location: Optional location to narrow search
        limit_reviews: Maximum number of reviews to retrieve (default: 5)
        language: Language code for reviews (default: "en")
    
    Returns:
        PlaceDetails object with latest reviews (sorted by time)
    """
    client = get_tripadvisor_client()
    return client.get_reviews(query, location=location, limit_reviews=limit_reviews, language=language)

