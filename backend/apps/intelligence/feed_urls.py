"""The student's "For you" feed, mounted at /api/v1/feed/ (see feed.py)."""

from django.urls import path

from .views import (
    DigestView,
    FeedDetailView,
    FeedDismissView,
    FeedFeedbackView,
    FeedListView,
    FeedReadView,
    HomeView,
    SearchView,
)

urlpatterns = [
    path("", FeedListView.as_view(), name="feed"),
    path("home/", HomeView.as_view(), name="feed-home"),
    path("search/", SearchView.as_view(), name="feed-search"),
    path("digest/", DigestView.as_view(), name="feed-digest"),
    path("<int:insight_id>/", FeedDetailView.as_view(), name="feed-item"),
    path("<int:insight_id>/read/", FeedReadView.as_view(), name="feed-read"),
    path("<int:insight_id>/dismiss/", FeedDismissView.as_view(), name="feed-dismiss"),
    path("<int:insight_id>/feedback/", FeedFeedbackView.as_view(), name="feed-feedback"),
]
