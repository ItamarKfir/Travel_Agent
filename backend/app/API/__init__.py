"""
API integrations module.

This module contains integrations with external APIs:
- Google Places API
- TripAdvisor API
"""
from .google_places import (
    GooglePlacesClient,
    get_google_places_client,
    get_place_reviews,
    Review as GoogleReview,
    PlaceDetails as GooglePlaceDetails
)

from .tripadvisor import (
    TripAdvisorClient,
    get_tripadvisor_client,
    get_location_reviews,
    Review as TripAdvisorReview,
    PlaceDetails as TripAdvisorPlaceDetails
)

__all__ = [
    "GooglePlacesClient",
    "get_google_places_client",
    "get_place_reviews",
    "GoogleReview",
    "GooglePlaceDetails",
    "TripAdvisorClient",
    "get_tripadvisor_client",
    "get_location_reviews",
    "TripAdvisorReview",
    "TripAdvisorPlaceDetails",
]
