"""Staff-area addresses for academics, mounted at /api/v1/manage/academics/."""

from rest_framework.routers import SimpleRouter

from .manage_views import ManageIntakeViewSet, ManageProgrammeViewSet, ManageSchoolViewSet

router = SimpleRouter()
router.register("schools", ManageSchoolViewSet, basename="manage-school")
router.register("programmes", ManageProgrammeViewSet, basename="manage-programme")
router.register("intakes", ManageIntakeViewSet, basename="manage-intake")

urlpatterns = router.urls
