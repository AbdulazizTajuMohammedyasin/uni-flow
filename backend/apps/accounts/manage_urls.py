"""Staff-area addresses for accounts, mounted at /api/v1/manage/ (see config/api_v1.py)."""

from rest_framework.routers import SimpleRouter

from .manage_views import ManageUserViewSet

router = SimpleRouter()
router.register("users", ManageUserViewSet, basename="manage-user")

urlpatterns = router.urls
