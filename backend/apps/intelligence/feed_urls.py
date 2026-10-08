"""The student's "For you" feed, mounted at /api/v1/feed/ (see feed.py)."""

from django.urls import path

from .views import FeedDetailView, FeedDismissView, FeedFeedbackView, FeedListView, FeedReadView

urlpatterns = [
    path("", FeedListView.as_view(), name="feed"),
    path("<int:insight_id>/", FeedDetailView.as_view(), name="feed-item"),
    path("<int:insight_id>/read/", FeedReadView.as_view(), name="feed-read"),
    path("<int:insight_id>/dismiss/", FeedDismissView.as_view(), name="feed-dismiss"),
    path("<int:insight_id>/feedback/", FeedFeedbackView.as_view(), name="feed-feedback"),
]
