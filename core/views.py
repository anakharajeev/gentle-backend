from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from django.db import models
from django.db.models import Count, Sum
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from datetime import date
from django.utils.timezone import localdate

from .models import Event, Donation
from .serializers import EventSerializer, DonationSerializer


# ==============================
# CUSTOM PERMISSIONS
# ==============================
class IsAdminOrHR(IsAuthenticated):
    """Admins + HR can create, update, delete events."""
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        user = request.user
        return user.is_superuser or user.is_staff  

# ==============================
# DONATION PAGINATION
# ==============================
class DonationPagination(PageNumberPagination):
    page_size_query_param = "page_size"

# ==============================
# EVENT LIST + SEARCH + FILTER
# ==============================
class EventListCreateView(generics.ListCreateAPIView):
    queryset = Event.objects.all().order_by('-date')
    serializer_class = EventSerializer
    filter_backends = [SearchFilter]
    search_fields = ['title', 'description', 'location']

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminOrHR()]
        return [IsAuthenticated()]


# ==============================
# EVENT DETAIL
# ==============================
class EventDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsAdminOrHR()]
        return [IsAuthenticated()]


# ==============================
# DONATION LIST + CREATE
# ==============================
class DonationListCreateView(generics.ListCreateAPIView):
    serializer_class = DonationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ["donor__username", "donor__email"]
    pagination_class = DonationPagination

    def get_queryset(self):
        return Donation.objects.filter(
            event_id=self.kwargs["event_id"]
        ).select_related("donor", "event").order_by("-date")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        event_id = self.kwargs.get("event_id")
        event = Event.objects.get(id=event_id)
        context["event"] = event  
        return context

    def perform_create(self, serializer):
        donation = serializer.save()

        # Send email after saving
        user = self.request.user
        if user.email:
            try:
                send_mail(
                    subject=f"Donation Successful - {donation.event.title}",
                    message=(
                        f"Hello {user.username},\n\n"
                        f"Thank you for donating ₹{donation.amount} to '{donation.event.title}'.\n"
                        f"Your donation has been successfully recorded.\n\n"
                        f"Regards,\nEvent Management Team"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception as e:
                print("Email send error:", e)

# ==============================
# USER PROFILE
# ==============================
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        groups = [g.name.lower() for g in user.groups.all()]

        if user.is_superuser:
            role = "admin"
        elif user.is_staff:
            role = "hr"
        else:
            role = "employee"

        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": role,
            "groups": groups,
        })


# ==============================
# DONATION SUMMARY VIEW
# ==============================
class DonationSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        search = request.GET.get("search", "")
        page = int(request.GET.get("page", 1))
        page_size = request.GET.get("page_size", "10")

        qs = Event.objects.all().order_by('-date')

        if search:
            qs = qs.filter(title__icontains=search)

        total = qs.count()

        if page_size != "all":
            page_size = int(page_size)
            start = (page - 1) * page_size
            end = start + page_size
            qs = qs[start:end]

        results = []
        today = localdate()

        for idx, event in enumerate(qs, start=1 + (page-1)*(page_size if page_size != "all" else total)):
            donation_agg = event.donations.aggregate(
                total_donations=Count("id"),
                total_amount=Sum("amount")
            )
            total_donations = donation_agg["total_donations"] or 0
            total_amount = donation_agg["total_amount"] or 0
            status = "Completed" if event.date < today else "Upcoming"
            results.append({
                "id": event.id,
                "name": event.title,
                "date": event.date,
                "count": total_donations,
                "amount": total_amount,
                "status": status,
                "hasDonation": total_donations > 0
            })

        return Response({
            "results": results,
            "total": total
        })
