from django.urls import include, path
from rest_framework.routers import DefaultRouter

from cms.api import contacts_settings, home_page
from projects.api import ProjectCategoryViewSet, ProjectViewSet
from rental.api import RentalCategoryViewSet, RentalItemViewSet


router = DefaultRouter()
router.register("projects/categories", ProjectCategoryViewSet, basename="project-categories")
router.register("projects", ProjectViewSet, basename="projects")
router.register("rental/categories", RentalCategoryViewSet, basename="rental-categories")
router.register("rental/items", RentalItemViewSet, basename="rental-items")

urlpatterns = [
    path("", include(router.urls)),
    path("pages/home/", home_page, name="api-home-page"),
    path("pages/contacts/", contacts_settings, name="api-contacts-page"),
]
