"""
Tool for fetching place reviews from Google Places and TripAdvisor APIs.

This tool combines reviews from both APIs and formats them in a clear,
structured way that's easy for LLMs to understand and use.
"""
import logging
from typing import Optional
from langchain_core.tools import tool

from app.API import get_place_reviews, get_location_reviews

logger = logging.getLogger(__name__)


def _format_place_reviews_output(
    source: str,
    place_name: str,
    address: Optional[str],
    rating: Optional[float],
    total_reviews: Optional[int],
    reviews: list,
    error: Optional[str] = None
) -> str:
    """
    Format place reviews data into a clear, structured string for LLM consumption.
    
    Args:
        source: API source name (e.g., "Google Places" or "TripAdvisor")
        place_name: Name of the place
        address: Address of the place
        rating: Overall rating
        total_reviews: Total number of reviews
        reviews: List of review objects
        error: Optional error message
        
    Returns:
        Formatted string with place information and reviews
    """
    output = f"\n{'='*60}\n"
    output += f"Source: {source}\n"
    
    if error:
        output += f"Status: ERROR - {error}\n"
        output += f"{'='*60}\n"
        return output
    
    output += f"Place: {place_name}\n"
    if address:
        output += f"Address: {address}\n"
    if rating is not None:
        output += f"Overall Rating: {rating}/5.0\n"
    if total_reviews is not None:
        output += f"Total Reviews: {total_reviews}\n"
    
    if not reviews:
        output += "Reviews: No reviews available\n"
    else:
        output += f"\nReviews ({len(reviews)} latest):\n"
        output += "-" * 60 + "\n"
        
        for i, review in enumerate(reviews, 1):
            output += f"\nReview {i}:\n"
            if review.rating is not None:
                output += f"  Rating: {review.rating}/5.0\n"
            output += f"  Review Text: {review.text}\n"
            if review.time:
                from datetime import datetime
                try:
                    review_date = datetime.fromtimestamp(review.time).strftime("%Y-%m-%d")
                    output += f"  Date: {review_date}\n"
                except:
                    pass
            if review.relative_time_description:
                output += f"  Posted: {review.relative_time_description}\n"
    
    output += f"\n{'='*60}\n"
    return output


@tool
def get_place_reviews_from_apis(
    place_name: str,
    location: Optional[str] = None
) -> str:
    """
    Get reviews for a place from both Google Places and TripAdvisor APIs.
    
    This tool searches for the place using both APIs and returns a formatted
    summary of reviews, ratings, and place information. If a location is not found,
    it provides helpful explanations to help correct the search.
    
    Args:
        place_name: The name of the place to search for (e.g., "Eiffel Tower", "Starbucks")
        location: Optional location context to narrow the search (e.g., "Paris, France", "New York, NY").
                  This helps when there are multiple places with the same name.
    
    Returns:
        A formatted string containing:
        - Place information (name, address, overall rating)
        - Latest reviews with ratings and text from both APIs
        - Error messages with explanations if location is not found
        
    Examples:
        - place_name="Eiffel Tower", location="Paris, France"
        - place_name="Central Park", location="New York"
        - place_name="Starbucks", location="Times Square, New York"
    """
    try:
        # Validate inputs
        if not place_name or not isinstance(place_name, str) or not place_name.strip():
            return ("ERROR: Invalid place_name. "
                   "Please provide a non-empty string with the name of the place. "
                   "Example: 'Eiffel Tower' or 'Central Park'")
        
        place_name = place_name.strip()
        
        # Initialize result strings
        google_output = ""
        tripadvisor_output = ""
        
        # Try Google Places API
        try:
            logger.info(f"Fetching Google Places reviews for: {place_name} ({location})")
            google_data = get_place_reviews(place_name)
            
            google_output = _format_place_reviews_output(
                source="Google Places",
                place_name=google_data.name,
                address=google_data.address,
                rating=google_data.rating,
                total_reviews=google_data.total_reviews,
                reviews=google_data.reviews
            )
            
        except ValueError as e:
            error_msg = str(e)
            logger.warning(f"Google Places error: {error_msg}")
            
            # Provide helpful error explanation
            if "not found" in error_msg.lower() or "place not found" in error_msg.lower():
                explanation = (
                    f"The place '{place_name}' was not found in Google Places. "
                    f"Possible reasons:\n"
                    f"1. The place name might be misspelled or incomplete\n"
                    f"2. The location context might be too specific or incorrect\n"
                    f"3. Try providing a more general location (e.g., 'Paris' instead of '123 Main St, Paris')\n"
                    f"4. Try a more complete place name (e.g., 'Eiffel Tower' instead of just 'Eiffel')\n"
                    f"5. The place might not exist in Google Places database"
                )
            else:
                explanation = f"Google Places API error: {error_msg}"
            
            google_output = _format_place_reviews_output(
                source="Google Places",
                place_name=place_name,
                address=None,
                rating=None,
                total_reviews=None,
                reviews=[],
                error=explanation
            )
            
        except Exception as e:
            error_msg = f"Unexpected error with Google Places API: {str(e)}"
            logger.error(error_msg, exc_info=True)
            google_output = _format_place_reviews_output(
                source="Google Places",
                place_name=place_name,
                address=None,
                rating=None,
                total_reviews=None,
                reviews=[],
                error=error_msg
            )
        
        # Try TripAdvisor API
        try:
            logger.info(f"Fetching TripAdvisor reviews for: {place_name} ({location})")
            tripadvisor_data = get_location_reviews(
                query=place_name,
                location=location,
                limit_reviews=5,
                language="en"
            )
            
            tripadvisor_output = _format_place_reviews_output(
                source="TripAdvisor",
                place_name=tripadvisor_data.name,
                address=tripadvisor_data.address,
                rating=tripadvisor_data.rating,
                total_reviews=tripadvisor_data.total_reviews,
                reviews=tripadvisor_data.reviews
            )
            
        except ValueError as e:
            error_msg = str(e)
            logger.warning(f"TripAdvisor error: {error_msg}")
            
            # Provide helpful error explanation
            if "not found" in error_msg.lower() or "location not found" in error_msg.lower():
                explanation = (
                    f"The location '{place_name}' was not found in TripAdvisor. "
                    f"Possible reasons:\n"
                    f"1. The place name might be misspelled or too vague\n"
                    f"2. The location parameter might need adjustment (e.g., try 'Paris, France' instead of just 'Paris')\n"
                    f"3. Try using the full official name of the place\n"
                    f"4. Some places might not be listed on TripAdvisor\n"
                    f"5. Verify the spelling of both place name and location"
                )
            else:
                explanation = f"TripAdvisor API error: {error_msg}"
            
            tripadvisor_output = _format_place_reviews_output(
                source="TripAdvisor",
                place_name=place_name,
                address=None,
                rating=None,
                total_reviews=None,
                reviews=[],
                error=explanation
            )
            
        except Exception as e:
            error_msg = f"Unexpected error with TripAdvisor API: {str(e)}"
            logger.error(error_msg, exc_info=True)
            tripadvisor_output = _format_place_reviews_output(
                source="TripAdvisor",
                place_name=place_name,
                address=None,
                rating=None,
                total_reviews=None,
                reviews=[],
                error=error_msg
            )
        
        # Combine results
        combined_output = "\nPLACE REVIEWS SUMMARY\n"
        combined_output += "=" * 60 + "\n"
        combined_output += f"Search Query: {place_name}"
        if location:
            combined_output += f" (in {location})"
        combined_output += "\n" + "=" * 60 + "\n"
        
        combined_output += google_output
        combined_output += "\n"
        combined_output += tripadvisor_output
        
        # Add summary
        combined_output += "\n" + "=" * 60 + "\n"
        combined_output += "SUMMARY:\n"
        combined_output += "This tool searched for reviews from both Google Places and TripAdvisor.\n"
        combined_output += "If either API returned an error, see the error explanation above.\n"
        combined_output += "If no reviews were found, the place might not exist or have reviews.\n"
        combined_output += "You can suggest the user try a different place name or location.\n"
        combined_output += "=" * 60 + "\n"
        
        return combined_output
        
    except Exception as e:
        error_msg = f"Unexpected error in get_place_reviews_from_apis: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return f"ERROR: {error_msg}. Please try again with a different place name or location."
