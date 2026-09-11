from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramSimilarity
from django.core.cache import cache
from django.db.models import Max, Min, Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_field
from rest_framework import serializers, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from rental.models import AttributeType, RentalAttribute, RentalCategory, RentalItem


ATTRIBUTE_PREFIX = "attributes."


def image_url(image):
    return image.file.url if image else None


class RentalCategoryTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = RentalCategory
        fields = ["title", "slug", "sort_order", "children"]

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_children(self, obj):
        children = obj.get_children().filter(is_active=True).order_by("path")
        return RentalCategoryTreeSerializer(children, many=True).data


class RentalCategorySerializer(serializers.ModelSerializer):
    parent_slug = serializers.SerializerMethodField()

    class Meta:
        model = RentalCategory
        fields = ["title", "slug", "parent_slug", "sort_order"]

    @extend_schema_field(OpenApiTypes.STR)
    def get_parent_slug(self, obj):
        parent = obj.get_parent()
        return parent.slug if parent else None


class RentalAttributeValueSerializer(serializers.Serializer):
    name = serializers.CharField(source="attribute.name")
    slug = serializers.CharField(source="attribute.slug")
    type = serializers.CharField(source="attribute.type")
    unit = serializers.CharField(source="attribute.unit")
    value = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.ANY)
    def get_value(self, obj):
        if obj.value_number is not None:
            return obj.value_number
        if obj.value_boolean is not None:
            return obj.value_boolean
        return obj.value_choice or obj.value_text


class RentalItemListSerializer(serializers.ModelSerializer):
    category = RentalCategorySerializer()
    main_image = serializers.SerializerMethodField()

    class Meta:
        model = RentalItem
        fields = [
            "title",
            "slug",
            "category",
            "short_description",
            "price",
            "price_on_request",
            "price_unit",
            "main_image",
            "status",
        ]

    @extend_schema_field(OpenApiTypes.URI)
    def get_main_image(self, obj):
        return image_url(obj.main_image)


class RentalItemDetailSerializer(RentalItemListSerializer):
    gallery = serializers.SerializerMethodField()
    attributes = RentalAttributeValueSerializer(source="attribute_values", many=True)
    video_url = serializers.SerializerMethodField()

    class Meta(RentalItemListSerializer.Meta):
        fields = RentalItemListSerializer.Meta.fields + [
            "description",
            "detail_description",
            "video_url",
            "seo_title",
            "seo_description",
            "gallery",
            "attributes",
        ]

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_gallery(self, obj):
        return [
            {
                "image": image_url(item.image),
                "caption": item.caption,
                "sort_order": item.sort_order,
            }
            for item in obj.gallery.all()
        ]

    @extend_schema_field(OpenApiTypes.URI)
    def get_video_url(self, obj):
        return obj.video_file.url if obj.video_file else obj.external_video_url


class RentalCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RentalCategoryTreeSerializer
    lookup_field = "slug"

    def get_queryset(self):
        queryset = RentalCategory.objects.filter(is_active=True).order_by("path")
        if self.action == "list":
            queryset = queryset.filter(depth=1)
        return queryset

    def list(self, request, *args, **kwargs):
        key = "api:rental:categories"
        data = cache.get(key)
        if data is None:
            data = self.get_serializer(self.get_queryset(), many=True).data
            cache.set(key, data, settings.CACHE_TIMEOUT)
        return Response(data)


class RentalItemViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "slug"

    def get_queryset(self):
        queryset = (
            RentalItem.objects.published()
            .filter(is_active=True, category__is_active=True)
            .select_related("category", "main_image")
            .prefetch_related("gallery__image", "attribute_values__attribute")
        )
        params = self.request.query_params
        if category_slug := params.get("category"):
            try:
                category = RentalCategory.objects.get(slug=category_slug, is_active=True)
            except RentalCategory.DoesNotExist:
                queryset = queryset.none()
            else:
                category_ids = [category.id, *category.get_descendants().filter(is_active=True).values_list("id", flat=True)]
                queryset = queryset.filter(category_id__in=category_ids)
        if status := params.get("status"):
            queryset = queryset.filter(status=status)
        if price_min := params.get("price_min"):
            queryset = queryset.filter(Q(price__gte=price_min) | Q(price_on_request=True))
        if price_max := params.get("price_max"):
            queryset = queryset.filter(Q(price__lte=price_max) | Q(price_on_request=True))
        queryset = apply_attribute_filters(queryset, params)
        if search := params.get("search"):
            vector = (
                SearchVector("title", weight="A")
                + SearchVector("short_description", weight="B")
                + SearchVector("description", weight="C")
                + SearchVector("category__title", weight="B")
                + SearchVector("attribute_values__value_text", weight="D")
                + SearchVector("attribute_values__value_choice", weight="D")
            )
            query = SearchQuery(search)
            queryset = (
                queryset.annotate(
                    search_rank=SearchRank(vector, query),
                    similarity=TrigramSimilarity("title", search),
                )
                .filter(Q(search_rank__gt=0.05) | Q(similarity__gt=0.15))
                .order_by("-search_rank", "-similarity", "sort_order", "title")
            )
        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return RentalItemDetailSerializer
        return RentalItemListSerializer


def apply_attribute_filters(queryset, params):
    for key, value in params.items():
        if not key.startswith(ATTRIBUTE_PREFIX) or value == "":
            continue
        expression = key.removeprefix(ATTRIBUTE_PREFIX)
        if expression.endswith("_min"):
            queryset = queryset.filter(
                attribute_values__attribute__slug=expression[:-4],
                attribute_values__attribute__type=AttributeType.NUMBER,
                attribute_values__value_number__gte=value,
            )
        elif expression.endswith("_max"):
            queryset = queryset.filter(
                attribute_values__attribute__slug=expression[:-4],
                attribute_values__attribute__type=AttributeType.NUMBER,
                attribute_values__value_number__lte=value,
            )
        else:
            queryset = filter_attribute_exact(queryset, expression, value)
    return queryset


def filter_attribute_exact(queryset, slug, value):
    try:
        attribute = RentalAttribute.objects.get(slug=slug)
    except RentalAttribute.DoesNotExist:
        return queryset.none()

    filters = {"attribute_values__attribute": attribute}
    if attribute.type == AttributeType.NUMBER:
        filters["attribute_values__value_number"] = value
    elif attribute.type == AttributeType.BOOLEAN:
        parsed = parse_bool(value)
        if parsed is None:
            return queryset.none()
        filters["attribute_values__value_boolean"] = parsed
    elif attribute.type == AttributeType.CHOICE:
        filters["attribute_values__value_choice"] = value
    else:
        filters["attribute_values__value_text"] = value
    return queryset.filter(**filters)


def parse_bool(value):
    lowered = str(value).lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    return None


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
def rental_filters(request):
    data = cache.get("api:rental:filters")
    if data is None:
        price_range = RentalItem.objects.published().filter(is_active=True, price_on_request=False).aggregate(
            min=Min("price"),
            max=Max("price"),
        )
        attributes = RentalAttribute.objects.filter(filterable=True).order_by("sort_order", "name")
        data = {
            "price": price_range,
            "attributes": [
                {
                    "name": item.name,
                    "slug": item.slug,
                    "type": item.type,
                    "unit": item.unit,
                }
                for item in attributes
            ],
        }
        cache.set("api:rental:filters", data, settings.CACHE_TIMEOUT)
    return Response(data)
