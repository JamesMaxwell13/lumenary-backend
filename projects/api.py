from django.conf import settings
from django.core.cache import cache
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers, viewsets
from rest_framework.response import Response

from cms.images import image_original_url, image_rendition_url
from cms.media import video_status
from projects.models import Project, ProjectCategory


PROJECT_COVER_RENDITION = "fill-1280x720"


class ProjectCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectCategory
        fields = ["title", "slug", "sort_order"]


class ProjectListSerializer(serializers.ModelSerializer):
    category = ProjectCategorySerializer()
    cover_image = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()
    video_status = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "title",
            "slug",
            "category",
            "cover_image",
            "video_url",
            "video_status",
            "short_caption",
            "is_featured",
        ]

    @extend_schema_field(OpenApiTypes.URI)
    def get_cover_image(self, obj):
        return image_rendition_url(obj.cover_image, PROJECT_COVER_RENDITION)

    @extend_schema_field(OpenApiTypes.URI)
    def get_video_url(self, obj):
        return obj.video_file.url if obj.video_file else obj.external_video_url

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_video_status(self, obj):
        return video_status(obj.video_file, obj.external_video_url)


class ProjectDetailSerializer(ProjectListSerializer):
    gallery = serializers.SerializerMethodField()

    class Meta(ProjectListSerializer.Meta):
        fields = ProjectListSerializer.Meta.fields + [
            "description",
            "client",
            "production_year",
            "role",
            "detail_title",
            "detail_text",
            "seo_title",
            "seo_description",
            "published_at",
            "gallery",
    ]

    @extend_schema_field(OpenApiTypes.URI)
    def get_cover_image(self, obj):
        return super().get_cover_image(obj)

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_gallery(self, obj):
        return [
            {
                "image": image_original_url(item.image),
                "caption": item.caption,
                "sort_order": item.sort_order,
            }
            for item in obj.gallery.all()
        ]


class ProjectCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProjectCategorySerializer
    lookup_field = "slug"

    def get_queryset(self):
        return ProjectCategory.objects.filter(is_active=True).order_by("sort_order", "title")

    def list(self, request, *args, **kwargs):
        key = "api:projects:categories"
        data = cache.get(key)
        if data is None:
            data = self.get_serializer(self.get_queryset(), many=True).data
            cache.set(key, data, settings.CACHE_TIMEOUT)
        return Response(data)


class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "slug"

    def get_queryset(self):
        queryset = (
            Project.objects.published()
            .filter(category__is_active=True)
            .select_related("category", "cover_image")
            .prefetch_related("gallery__image")
        )
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category__slug=category)
        featured = self.request.query_params.get("featured")
        if featured in {"1", "true"}:
            queryset = queryset.filter(is_featured=True)
        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProjectDetailSerializer
        return ProjectListSerializer
