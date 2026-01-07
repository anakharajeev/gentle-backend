from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    EventListCreateView,
    EventDetailView,
    DonationListCreateView,
    UserProfileView,
    DonationSummaryView,  
)

urlpatterns = [
    # ============================
    # AUTH (JWT)
    # ============================
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # ============================
    # EVENTS
    # ============================
    path("events/", EventListCreateView.as_view(), name="event_list_create"),
    path("events/<int:pk>/", EventDetailView.as_view(), name="event_detail"),

    # ============================
    # DONATIONS FOR AN EVENT 
    # ============================
    path(
        "events/<int:event_id>/donations/",
        DonationListCreateView.as_view(),
        name="donation_list_create",
    ),

    # ============================
    # DONATIONS SUMMARY 
    # ============================
    path(
        "donations/summary/",
        DonationSummaryView.as_view(),
        name="donation_summary",
    ),

    # ============================
    # USER PROFILE
    # ============================
    path("user/", UserProfileView.as_view(), name="user_profile"),
]
