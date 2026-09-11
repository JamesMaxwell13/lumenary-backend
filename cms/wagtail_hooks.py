from django import forms
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from projects.models import Project, ProjectCategory
from rental.models import RentalAttribute, RentalCategory, RentalItem
from services.models import ServiceBlock


class ServiceBlockViewSet(SnippetViewSet):
    model = ServiceBlock
    menu_label = "Services"
    menu_icon = "list-ul"
    list_display = ["title", "sort_order", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["title", "text"]
    ordering = ["sort_order", "title"]


class ProjectCategoryViewSet(SnippetViewSet):
    model = ProjectCategory
    menu_label = "Project categories"
    menu_icon = "folder-open-inverse"
    list_display = ["title", "slug", "sort_order", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["title", "slug"]
    ordering = ["sort_order", "title"]


class ProjectViewSet(SnippetViewSet):
    model = Project
    menu_label = "Projects"
    menu_icon = "folder-open-inverse"
    list_display = ["title", "category", "status", "is_featured", "published_at"]
    list_filter = ["category", "status", "is_featured"]
    search_fields = ["title", "slug", "short_caption", "description", "client"]
    ordering = ["sort_order", "-published_at", "title"]


class RentalCategoryForm(forms.ModelForm):
    parent = forms.ModelChoiceField(
        label="Parent category",
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
    menu_label = "Rental categories"
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
    menu_label = "Rental items"
    menu_icon = "pick"
    list_display = ["title", "category", "status", "publication_status", "is_active", "price"]
    list_filter = ["category", "status", "publication_status", "is_active", "price_on_request"]
    search_fields = ["title", "slug", "short_description", "description", "detail_description"]
    ordering = ["sort_order", "title"]


class RentalAttributeViewSet(SnippetViewSet):
    model = RentalAttribute
    menu_label = "Rental attributes"
    menu_icon = "list-ul"
    list_display = ["name", "slug", "type", "filterable", "sort_order"]
    list_filter = ["type", "filterable"]
    search_fields = ["name", "slug", "unit"]
    ordering = ["sort_order", "name"]


register_snippet(ServiceBlock, viewset=ServiceBlockViewSet)
register_snippet(ProjectCategory, viewset=ProjectCategoryViewSet)
register_snippet(Project, viewset=ProjectViewSet)
register_snippet(RentalCategory, viewset=RentalCategoryViewSet)
register_snippet(RentalItem, viewset=RentalItemViewSet)
register_snippet(RentalAttribute, viewset=RentalAttributeViewSet)
