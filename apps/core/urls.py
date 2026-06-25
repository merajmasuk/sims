from rest_framework.routers import DefaultRouter
from views import DepartmentViewSet, ProgramViewSet, AcademicTermViewSet

router = DefaultRouter()
router.register(r"departments", DepartmentViewSet, basename="department")
router.register(r"programs", ProgramViewSet, basename="program")
router.register(r"academic-terms", AcademicTermViewSet, basename="academic-term")

urlpatterns = router.urls
