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
        
        # Try TripAdvisor API - Use Google Places address if available for better accuracy
        tripadvisor_data = None
        tripadvisor_place_data = None
        tripadvisor_output = ""
        
        if google_place_data and google_place_data.get("address"):
            # Strategy: Use Google Places address to extract location for TripAdvisor search
            google_address = google_place_data["address"]
            google_name = google_place_data["name"]
            
            # Extract city and country from Google Places address for TripAdvisor location
            # Format: "Street, City, Postal, Country" or "Street, City, Country"
            address_parts = [part.strip() for part in google_address.split(",")]
            
            # Extract city and country (usually last two parts)
            if len(address_parts) >= 2:
                # Try different combinations
                location_attempts = []
                
                # Attempt 1: City, Country (most common)
                if len(address_parts) >= 2:
                    location_attempts.append(f"{address_parts[-2]}, {address_parts[-1]}")
                
                # Attempt 2: Just city if country is obvious
                if len(address_parts) >= 2:
                    location_attempts.append(address_parts[-2])
                
                # Attempt 3: Use provided location if available
                if location:
                    location_attempts.append(location)
                
                # Remove duplicates while preserving order
                seen = set()
                unique_location_attempts = []
                for loc in location_attempts:
                    if loc not in seen:
                        seen.add(loc)
                        unique_location_attempts.append(loc)
                location_attempts = unique_location_attempts
                
                # Try TripAdvisor search with Google Places name and extracted location
                tripadvisor_query = google_name
                
                for attempt_num, location_attempt in enumerate(location_attempts, 1):
                    try:
                        logger.info(f"TripAdvisor attempt {attempt_num}: query='{tripadvisor_query}', location='{location_attempt}'")
                        tripadvisor_data = get_location_reviews(
                            query=tripadvisor_query,
                            location=location_attempt,
                            limit_reviews=5,
                            language="en"
                        )
                        
                        tripadvisor_place_data = {
                            "name": tripadvisor_data.name,
                            "address": tripadvisor_data.address,
                            "rating": tripadvisor_data.rating
                        }
                        logger.info(f"TripAdvisor search succeeded: '{tripadvisor_data.name}'")
                        break
                    except Exception as e:
                        logger.debug(f"TripAdvisor attempt {attempt_num} failed: {e}")
                        if attempt_num == len(location_attempts):
                            # Last attempt failed
                            raise
                        continue
            else:
                # Fallback: Use original parameters
                try:
                    logger.info(f"TripAdvisor search with original parameters: query='{google_name}', location='{location}'")
                    tripadvisor_data = get_location_reviews(
                        query=google_name,
                        location=location,
                        limit_reviews=5,
                        language="en"
                    )
                    tripadvisor_place_data = {
                        "name": tripadvisor_data.name,
                        "address": tripadvisor_data.address,
                        "rating": tripadvisor_data.rating
                    }
                except Exception as e:
                    logger.warning(f"TripAdvisor search failed: {e}")
                    tripadvisor_data = None
        
        else:
            # Fallback to original parameters if Google Places failed or no address
            try:
                logger.info(f"TripAdvisor search with original parameters: query='{place_name}', location='{location}'")
                tripadvisor_data = get_location_reviews(
                    query=place_name,
                    location=location,
                    limit_reviews=5,
                    language="en"
                )
                tripadvisor_place_data = {
                    "name": tripadvisor_data.name,
                    "address": tripadvisor_data.address,
                    "rating": tripadvisor_data.rating
                }
            except Exception as e:
                logger.warning(f"TripAdvisor search failed: {e}")
                tripadvisor_data = None
        
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
        # Use address matching as the primary indicator (addresses are more reliable than names)
        places_match = True
        if google_place_data and tripadvisor_place_data:
            google_addr = (google_place_data.get("address") or "").lower()
            tripadvisor_addr = (tripadvisor_place_data.get("address") or "").lower()
            
            # Normalize addresses for comparison (remove common variations)
            def normalize_address(addr: str) -> str:
                """Normalize address for comparison by removing common variations."""
                normalized = addr.lower()
                # Remove common suffixes and variations
                normalized = normalized.replace(" street", " st")
                normalized = normalized.replace(" avenue", " ave")
                normalized = normalized.replace(" road", " rd")
                normalized = normalized.replace(" boulevard", " blvd")
                # Remove extra spaces
                normalized = " ".join(normalized.split())
                # Remove punctuation differences
                normalized = normalized.replace(".", "").replace(",", "")
                return normalized.strip()
            
            google_addr_normalized = normalize_address(google_addr) if google_addr else ""
            tripadvisor_addr_normalized = normalize_address(tripadvisor_addr) if tripadvisor_addr else ""
            
            # Extract street number and name for comparison (more reliable than full address)
            def extract_street_info(addr: str) -> tuple:
                """Extract street number and street name from address."""
                if not addr:
                    return ("", "")
                parts = addr.split(",")
                street_part = parts[0].strip() if parts else ""
                # Extract number and street name (e.g., "19 Hayarkon St" or "19 Hayarkon Street")
                words = street_part.split()
                if words and words[0].isdigit():
                    street_num = words[0]
                    street_name = " ".join(words[1:]).lower()
                    # Normalize street name - convert to lowercase and remove common suffixes
                    # Remove street type suffixes for comparison (keep the core name)
                    street_name = street_name.replace(" street", "").replace(" st", "").replace(" avenue", "").replace(" ave", "").replace(" road", "").replace(" rd", "")
                    street_name = street_name.strip()
                    return (street_num, street_name)
                return ("", street_part.lower())
            
            google_street = extract_street_info(google_addr)
            tripadvisor_street = extract_street_info(tripadvisor_addr)
            
            # Check if addresses match (same street number and name = same place)
            addresses_match = False
            if google_street[0] and tripadvisor_street[0]:  # Both have street numbers
                # Same street number and similar street name = same place
                if google_street[0] == tripadvisor_street[0]:
                    # Check if street names are similar (allow for minor variations)
                    google_street_words = set(google_street[1].split())
                    tripadvisor_street_words = set(tripadvisor_street[1].split())
                    # If significant words overlap, it's likely the same street
                    common_words = google_street_words.intersection(tripadvisor_street_words)
                    # Filter out very short words (a, the, etc.)
                    common_words = {w for w in common_words if len(w) > 2}
                    if common_words:
                        addresses_match = True
            elif google_addr_normalized and tripadvisor_addr_normalized:
                # No street numbers, but check if normalized addresses are similar
                # Check if they share significant words
                google_words = set(google_addr_normalized.split())
                tripadvisor_words = set(tripadvisor_addr_normalized.split())
                common_words = google_words.intersection(tripadvisor_words)
                # Filter out very short/common words
                common_words = {w for w in common_words if len(w) > 3 and w not in ["the", "and", "at"]}
                # If addresses share significant location words (city, street name, etc.), likely same place
                if len(common_words) >= 2:  # At least 2 significant words match
                    addresses_match = True
            
            # If addresses match (same location), it's the same place regardless of name differences
            if addresses_match:
                places_match = True
            else:
                # Addresses don't match - check names as secondary indicator
                google_name = google_place_data["name"].lower().strip()
                tripadvisor_name = tripadvisor_place_data["name"].lower().strip()
                
                # If names are very similar, might still be same place (address might be formatted differently)
                name_words_google = set(w for w in google_name.split() if len(w) > 3)
                name_words_tripadvisor = set(w for w in tripadvisor_name.split() if len(w) > 3)
                common_name_words = name_words_google.intersection(name_words_tripadvisor)
                
                if len(common_name_words) >= 2:  # Multiple significant words match
                    # Names match well - might be same place, address format difference
                    places_match = True
                else:
                    # Different addresses and different names = likely different places
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
