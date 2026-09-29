"""A pretend post type, only for testing the shared base (it never exists outside tests).

Its table is created by backend/conftest.py once the test database is ready.
"""

from apps.publishing.models import TargetedModel


class SamplePost(TargetedModel):
    class Meta(TargetedModel.Meta):
        app_label = "publishing"
        managed = False  # no migration; see backend/conftest.py
