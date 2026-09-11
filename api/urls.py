from django.urls import include, path
from rest_framework.routers import DefaultRouter

from cms.api import contacts_settings, footer_settings, home_page, services_page
from leads.api import ContactLeadCreateView
from projects.api import ProjectCategoryViewSet, ProjectViewSet
from rental.api import RentalCategoryViewSet, RentalItemViewSet, rental_filters
from leads.api import RentalLeadCreateView


router = DefaultRouter()
router.register("projects/categories", ProjectCategoryViewSet, basename="project-categories")
router.register("projects", ProjectViewSet, basename="projects")
router.register("rental/categories", RentalCategoryViewSet, basename="rental-categories")
router.register("rental/items", RentalItemViewSet, basename="rental-items")

urlpatterns = [
    path("", include(router.urls)),
    path("pages/home/", home_page, name="api-home-page"),
    path("pages/services/", services_page, name="api-services-page"),
    path("pages/contacts/", contacts_settings, name="api-contacts-page"),
    path("settings/footer/", footer_settings, name="api-footer-settings"),
    path("rental/filters/", rental_filters, name="api-rental-filters"),
    path("rental/leads/", RentalLeadCreateView.as_view(), name="api-rental-leads"),
    path("leads/", ContactLeadCreateView.as_view(), name="api-contact-leads"),
]
