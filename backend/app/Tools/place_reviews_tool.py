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
    
    # Show address FIRST and prominently for location confirmation
    if address:
        output += f"📍 ADDRESS: {address}\n"
        output += "-" * 60 + "\n"
    output += f"Place Name: {place_name}\n"
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
        
        # Store place data for comparison
        google_place_data = None
        tripadvisor_place_data = None
        
        # Try Google Places API
        try:
            logger.info(f"Fetching Google Places reviews for: {place_name} ({location})")
            google_data = get_place_reviews(place_name)
            
            google_place_data = {
                "name": google_data.name,
                "address": google_data.address,
                "rating": google_data.rating
            }
            
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
        
        # Try TripAdvisor API - Use Google Places results if available for better accuracy
        tripadvisor_data = None
        tripadvisor_place_data = None
        tripadvisor_output = ""
        
        # Prepare TripAdvisor search parameters
        # Priority: Use Google Places name and location if available (more accurate)
        if google_place_data:
            # Extract location from Google Places address or use provided location
            google_location = None
            if google_place_data.get("address"):
                # Extract city from address (e.g., "Tel Aviv-Yafo" from "HaYarkon St 205, Tel Aviv-Yafo, 6340506, Israel")
                address_parts = google_place_data["address"].split(",")
                if len(address_parts) >= 2:
                    # Try to get city name
                    city_part = address_parts[-2].strip() if len(address_parts) >= 2 else None
                    country_part = address_parts[-1].strip() if len(address_parts) >= 1 else None
                    if city_part and country_part:
                        google_location = f"{city_part}, {country_part}"
            
            # Use Google Places name and location for TripAdvisor search
            tripadvisor_query = google_place_data["name"]
            tripadvisor_location = google_location or location
            
            logger.info(f"Using Google Places data for TripAdvisor search: query='{tripadvisor_query}', location='{tripadvisor_location}'")
        else:
            # Fallback to original parameters if Google Places failed
            tripadvisor_query = place_name
            tripadvisor_location = location
            logger.info(f"Using original parameters for TripAdvisor search: query='{tripadvisor_query}', location='{tripadvisor_location}'")
        
        # First attempt for TripAdvisor
        try:
            logger.info(f"TripAdvisor attempt 1: query='{tripadvisor_query}', location='{tripadvisor_location}'")
            tripadvisor_data = get_location_reviews(
                query=tripadvisor_query,
                location=tripadvisor_location,
                limit_reviews=5,
                language="en"
            )
            
            tripadvisor_place_data = {
                "name": tripadvisor_data.name,
                "address": tripadvisor_data.address,
                "rating": tripadvisor_data.rating
            }
            
            # Check if TripAdvisor result matches Google Places (if available)
            if google_place_data:
                # Simple matching: check if place names are similar
                google_name_lower = google_place_data["name"].lower()
                tripadvisor_name_lower = tripadvisor_data.name.lower()
                
                # Check if TripAdvisor returned a generic location instead of the specific place
                # If Google found a specific hotel but TripAdvisor found a city/generic location, try again
                is_generic_location = (
                    tripadvisor_name_lower == tripadvisor_location.lower().split(",")[0].strip().lower() or
                    tripadvisor_name_lower in ["tel aviv", "milan", "paris", "new york"] or
                    len(tripadvisor_data.name.split()) <= 2  # Very short names might be generic
                )
                
                # Check if names don't match at all
                name_match = (
                    any(word in tripadvisor_name_lower for word in google_name_lower.split() if len(word) > 3) or
                    any(word in google_name_lower for word in tripadvisor_name_lower.split() if len(word) > 3)
                )
                
                if is_generic_location or not name_match:
                    logger.warning(f"TripAdvisor attempt 1 returned non-matching result: '{tripadvisor_data.name}' vs Google '{google_place_data['name']}'. Trying attempt 2...")
                    # Try second attempt with extracted place name
                    raise ValueError("Result doesn't match Google Places, trying different search")
            
        except (ValueError, Exception) as e:
            # Second attempt: Extract just the main place name (remove location info)
            if google_place_data:
                # Extract just the hotel/place name (e.g., "Hilton" from "Hilton Tel Aviv")
                google_name = google_place_data["name"]
                # Try to extract the brand/place name (usually first word or two)
                name_words = google_name.split()
                
                # Try different strategies
                attempts = [
                    # Try just the first word (e.g., "Hilton" from "Hilton Tel Aviv")
                    (" ".join(name_words[:1]), tripadvisor_location),
                    # Try first two words (e.g., "DoubleTree by" from "DoubleTree by Hilton")
                    (" ".join(name_words[:2]), tripadvisor_location) if len(name_words) >= 2 else None,
                ]
                
                # Filter out None attempts
                attempts = [a for a in attempts if a is not None]
                
                for attempt_num, (query_attempt, location_attempt) in enumerate(attempts, start=2):
                    try:
                        logger.info(f"TripAdvisor attempt {attempt_num}: query='{query_attempt}', location='{location_attempt}'")
                        tripadvisor_data = get_location_reviews(
                            query=query_attempt,
                            location=location_attempt,
                            limit_reviews=5,
                            language="en"
                        )
                        
                        # Check if this result is better
                        tripadvisor_name_lower = tripadvisor_data.name.lower()
                        google_name_lower = google_name.lower()
                        
                        # Check if it matches better
                        name_match = (
                            any(word in tripadvisor_name_lower for word in google_name_lower.split() if len(word) > 3) or
                            any(word in google_name_lower for word in tripadvisor_name_lower.split() if len(word) > 3)
                        )
                        
                        if name_match and not tripadvisor_name_lower == location_attempt.lower().split(",")[0].strip().lower():
                            logger.info(f"TripAdvisor attempt {attempt_num} succeeded with better match: '{tripadvisor_data.name}'")
                            tripadvisor_place_data = {
                                "name": tripadvisor_data.name,
                                "address": tripadvisor_data.address,
                                "rating": tripadvisor_data.rating
                            }
                            break
                    except Exception as e2:
                        logger.debug(f"TripAdvisor attempt {attempt_num} failed: {e2}")
                        continue
                else:
                    # All attempts failed, use the first result if we have it, otherwise raise
                    if tripadvisor_data is None:
                        # Set tripadvisor_data to None to trigger error handling below
                        pass
                    # Otherwise, use the first result even if it doesn't match perfectly
                    elif tripadvisor_place_data is None:
                        # If we have tripadvisor_data but haven't set tripadvisor_place_data, set it now
                        tripadvisor_place_data = {
                            "name": tripadvisor_data.name,
                            "address": tripadvisor_data.address,
                            "rating": tripadvisor_data.rating
                        }
            
            # If google_place_data is None, we don't have a second attempt strategy, just handle error normally
            elif tripadvisor_data is None:
                # This means the first attempt failed and we don't have Google Places data for a second attempt
                raise ValueError("Location not found on TripAdvisor")
        
        # Format TripAdvisor output if we have data
        if tripadvisor_data:
            tripadvisor_output = _format_place_reviews_output(
                source="TripAdvisor",
                place_name=tripadvisor_data.name,
                address=tripadvisor_data.address,
                rating=tripadvisor_data.rating,
                total_reviews=tripadvisor_data.total_reviews,
                reviews=tripadvisor_data.reviews
            )
        
        # Handle TripAdvisor errors
        if tripadvisor_data is None:
            # This means all attempts failed
            error_msg = "Location not found on TripAdvisor after multiple search attempts"
            logger.warning(f"TripAdvisor error: {error_msg}")
            
            explanation = (
                f"The place could not be found in TripAdvisor after trying multiple search strategies. "
                f"This might mean:\n"
                f"1. The place doesn't exist in TripAdvisor's database\n"
                f"2. The place name or location might need to be different on TripAdvisor\n"
                f"3. Try searching TripAdvisor directly with the place name"
            )
            
            tripadvisor_output = _format_place_reviews_output(
                source="TripAdvisor",
                place_name=place_name,
                address=None,
                rating=None,
                total_reviews=None,
                reviews=[],
                error=explanation
            )
        
        # Check if different places were found
        places_match = True
        if google_place_data and tripadvisor_place_data:
            # Compare place names (case-insensitive, remove common suffixes)
            google_name = google_place_data["name"].lower().strip()
            tripadvisor_name = tripadvisor_place_data["name"].lower().strip()
            
            # Simple comparison - check if names are similar (not exact match needed, but should be close)
            # Remove common words and compare core parts
            if google_name != tripadvisor_name:
                # Check if one is clearly different (not just minor variation)
                # If addresses are very different, they're likely different places
                google_addr = (google_place_data.get("address") or "").lower()
                tripadvisor_addr = (tripadvisor_place_data.get("address") or "").lower()
                
                # If names don't match and addresses don't match, likely different places
                if google_addr and tripadvisor_addr and google_addr != tripadvisor_addr:
                    places_match = False
        
        # Extract location and rating information from stored data or outputs
        google_address = google_place_data.get("address") if google_place_data else None
        google_rating = google_place_data.get("rating") if google_place_data else None
        google_name = google_place_data.get("name") if google_place_data else None
        
        tripadvisor_address = tripadvisor_place_data.get("address") if tripadvisor_place_data else None
        tripadvisor_rating = tripadvisor_place_data.get("rating") if tripadvisor_place_data else None
        tripadvisor_name = tripadvisor_place_data.get("name") if tripadvisor_place_data else None
        
        # Combine results with location and rating summary at the top
        combined_output = "\nPLACE REVIEWS SUMMARY\n"
        combined_output += "=" * 60 + "\n"
        combined_output += f"Search Query: {place_name}"
        if location:
            combined_output += f" (in {location})"
        combined_output += "\n" + "=" * 60 + "\n"
        
        # Warning if different places were found
        if not places_match and google_place_data and tripadvisor_place_data:
            combined_output += "\n⚠️ WARNING: DIFFERENT PLACES FOUND\n"
            combined_output += "Google Places and TripAdvisor returned different locations:\n"
            combined_output += f"  • Google Places: {google_name} at {google_address or 'Address not available'}\n"
            combined_output += f"  • TripAdvisor: {tripadvisor_name} at {tripadvisor_address or 'Address not available'}\n"
            combined_output += "Please note these are DIFFERENT places. Provide information separately and ask the user which one they want details about.\n"
            combined_output += "-" * 60 + "\n\n"
        
        # Show location information and ratings at the top
        combined_output += "\n📍 LOCATION INFORMATION:\n"
        if google_name and google_address:
            combined_output += f"  📍 Google Places:\n"
            combined_output += f"     Name: {google_name}\n"
            combined_output += f"     Address: {google_address}\n"
            if google_rating is not None:
                combined_output += f"     Rating: {google_rating}/5.0\n"
        if tripadvisor_name and tripadvisor_address:
            combined_output += f"  📍 TripAdvisor:\n"
            combined_output += f"     Name: {tripadvisor_name}\n"
            combined_output += f"     Address: {tripadvisor_address}\n"
            if tripadvisor_rating is not None:
                combined_output += f"     Rating: {tripadvisor_rating}/5.0\n"
        
        # Show combined average only if same place
        if places_match and google_rating is not None and tripadvisor_rating is not None:
            avg_rating = (google_rating + tripadvisor_rating) / 2
            combined_output += f"  • Average Rating: {avg_rating:.1f}/5.0\n"
        
        combined_output += "\n" + "-" * 60 + "\n\n"
        
        combined_output += google_output
        combined_output += "\n"
        combined_output += tripadvisor_output
        
        # Add summary
        combined_output += "\n" + "=" * 60 + "\n"
        combined_output += "SUMMARY:\n"
        combined_output += "This tool searched for reviews from both Google Places and TripAdvisor.\n"
        if not places_match:
            combined_output += "⚠️ IMPORTANT: Different places were found. Clearly indicate this to the user and separate the information for each place.\n"
            combined_output += "IMPORTANT: Ask the user which place they're interested in, or if they want details about both.\n"
        else:
            combined_output += "The address(es) and ratings shown above indicate the location found.\n"
        combined_output += "If either API returned an error, see the error explanation above.\n"
        combined_output += "If no reviews were found, the place might not exist or have reviews.\n"
        combined_output += "You can suggest the user try a different place name or location.\n"
        combined_output += "=" * 60 + "\n"
        
        return combined_output
        
    except Exception as e:
        error_msg = f"Unexpected error in get_place_reviews_from_apis: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return f"ERROR: {error_msg}. Please try again with a different place name or location."
