from django import forms
from django.templatetags.static import static
from django.urls import reverse
from django.utils.html import format_html
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

from cms.models import HomePage
from projects.models import Project, ProjectCategory
from rental.models import RentalAttribute, RentalCategory, RentalItem
from services.models import ServiceBlock


class ServiceBlockViewSet(SnippetViewSet):
    model = ServiceBlock
    menu_label = "Услуги"
    menu_name = "services-content"
    menu_icon = "list-ul"
    menu_order = 200
    add_to_admin_menu = True
    list_display = ["title", "sort_order", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["title", "text"]
    ordering = ["sort_order", "title"]


class ProjectCategoryViewSet(SnippetViewSet):
    model = ProjectCategory
    menu_label = "Разделы проектов"
    menu_name = "project-categories"
    menu_icon = "folder-open-inverse"
    list_display = ["title", "slug", "sort_order", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["title", "slug"]
    ordering = ["sort_order", "title"]


class ProjectViewSet(SnippetViewSet):
    model = Project
    menu_label = "Проекты"
    menu_name = "projects"
    menu_icon = "media"
    list_display = ["title", "category", "status", "is_featured", "published_at"]
    list_filter = ["category", "status", "is_featured"]
    search_fields = ["title", "slug", "short_caption", "description", "client"]
    ordering = ["sort_order", "-published_at", "title"]


class RentalCategoryForm(forms.ModelForm):
    parent = forms.ModelChoiceField(
        label="Родительский раздел",
        queryset=RentalCategory.objects.none(),
        required=False,
    )

    class Meta:
        model = RentalCategory
        fields = ["title", "slug", "parent", "sort_order", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = RentalCategory.objects.all().order_by("path")
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
            descendants = self.instance.get_descendants().values_list("pk", flat=True)
            queryset = queryset.exclude(pk__in=descendants)
        self.fields["parent"].queryset = queryset
        if self.instance.pk:
            self.initial["parent"] = self.instance.get_parent()

    def save(self, commit=True):
        parent = self.cleaned_data.pop("parent", None)
        instance = super().save(commit=False)
        moved = False
        if not instance.pk:
            if parent:
                instance = parent.add_child(instance=instance)
            else:
                instance = RentalCategory.add_root(instance=instance)
        elif parent != instance.get_parent():
            target = parent or instance.get_root()
            instance.move(target, pos="sorted-child" if parent else "sorted-sibling")
            moved = True
        if commit:
            if moved:
                instance.save(update_fields=["title", "slug", "sort_order", "is_active"])
            else:
                instance.save()
        return instance


class RentalCategoryViewSet(SnippetViewSet):
    model = RentalCategory
    menu_label = "Разделы аренды"
    menu_name = "rental-categories"
    menu_icon = "folder-open-inverse"
    list_display = ["title", "slug", "depth", "sort_order", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["title", "slug"]
    ordering = ["path"]
    form_class = RentalCategoryForm

    def get_form_class(self, for_update=False):
        return self.form_class


class RentalItemViewSet(SnippetViewSet):
    model = RentalItem
    menu_label = "Позиции аренды"
    menu_name = "rental-items"
    menu_icon = "pick"
    list_display = ["title", "category", "status", "publication_status", "price"]
    list_filter = ["category", "status", "publication_status", "price_on_request"]
    search_fields = ["title", "slug", "short_description", "description", "detail_description"]
    ordering = ["sort_order", "title"]


class RentalAttributeViewSet(SnippetViewSet):
    model = RentalAttribute
    menu_label = "Характеристики"
    menu_name = "rental-attributes"
    menu_icon = "list-ul"
    list_display = ["name", "slug", "type", "filterable", "sort_order"]
    list_filter = ["type", "filterable"]
    search_fields = ["name", "slug", "unit"]
    ordering = ["sort_order", "name"]


class PortfolioGroup(SnippetViewSetGroup):
    menu_label = "Проекты"
    menu_name = "portfolio"
    menu_icon = "media"
    menu_order = 300
    items = (ProjectViewSet, ProjectCategoryViewSet)


class RentalGroup(SnippetViewSetGroup):
    menu_label = "Аренда"
    menu_name = "rental-content"
    menu_icon = "pick"
    menu_order = 400
    items = (RentalItemViewSet, RentalCategoryViewSet, RentalAttributeViewSet)


SITE_MENU_ORDER = {
    "home": 100,
    "services-content": 200,
    "portfolio": 300,
    "rental-content": 400,
    "contacts": 500,
    "site-copy": 600,
}


@hooks.register("insert_global_admin_css")
def global_admin_css():
    return format_html('<link rel="stylesheet" href="{}">', static("cms/admin/branding.css"))


@hooks.register("insert_global_admin_js")
def global_admin_js():
    return format_html('<script src="{}"></script>', static("cms/admin/branding.js"))


@hooks.register("register_admin_menu_item")
def register_home_page_menu_item():
    home_page = HomePage.objects.live().first() or HomePage.objects.first()
    if home_page:
        url = reverse("wagtailadmin_pages:edit", args=[home_page.pk])
    else:
        url = reverse("wagtailadmin_explore_root")
    return MenuItem("Главная", url, icon_name="home", name="home", order=SITE_MENU_ORDER["home"])


@hooks.register("register_admin_menu_item")
def register_contacts_menu_item():
    url = reverse("wagtailsettings:edit", args=["cms", "contactsettings"])
    return MenuItem("Контакты", url, icon_name="mail", name="contacts", order=SITE_MENU_ORDER["contacts"])


@hooks.register("register_admin_menu_item")
def register_site_copy_menu_item():
    url = reverse("wagtailsettings:edit", args=["cms", "mainpagesectionsettings"])
    return MenuItem(
        "Заголовки",
        url,
        icon_name="doc-full",
        name="site-copy",
        order=SITE_MENU_ORDER["site-copy"],
    )


@hooks.register("construct_main_menu")
def arrange_main_menu(request, menu_items):
    menu_items[:] = [item for item in menu_items if item.name != "explorer"]
    for item in menu_items:
        if item.name in SITE_MENU_ORDER:
            item.order = SITE_MENU_ORDER[item.name]
        else:
            item.order = max(item.order, 1000)


@hooks.register("register_admin_viewset")
def register_services_viewset():
    return ServiceBlockViewSet()


@hooks.register("register_admin_viewset")
def register_portfolio_group():
    return PortfolioGroup()


@hooks.register("register_admin_viewset")
def register_rental_group():
    return RentalGroup()
