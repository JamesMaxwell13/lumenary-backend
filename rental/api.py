from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_field
from rest_framework import serializers, viewsets
from rest_framework.response import Response

from cms.images import image_original_url, image_rendition_url
from rental.models import RentalCategory, RentalItem


RENTAL_MAIN_IMAGE_RENDITION = "fill-1200x900"


EN_TO_RU_LAYOUT = str.maketrans(
    "`qwertyuiop[]asdfghjkl;'zxcvbnm,./"
    "~QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>?",
    "ёйцукенгшщзхъфывапролджэячсмитьбю."
    "ЁЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,"
)
RU_TO_EN_LAYOUT = str.maketrans(
    "ёйцукенгшщзхъфывапролджэячсмитьбю."
    "ЁЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,",
    "`qwertyuiop[]asdfghjkl;'zxcvbnm,./"
    "~QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>?"
)

RU_TO_LATIN = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "c",
    "ч": "ch",
    "ш": "sh",
    "щ": "sch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}
LATIN_TO_RU_HINTS = {
    "stand": "стенд",
    "stands": "стойки",
    "c-stand": "си стенд",
    "c stand": "си стенд",
    "grip": "грип",
    "flag": "флаг",
    "frame": "рама",
    "butterfly": "баттерфляй",
    "avenger": "авенджер",
    "manfrotto": "манфротто",
    "matthews": "мэтьюс",
}
RU_TO_LATIN_HINTS = {
    "си стенд": "c stand",
    "с-стенд": "c-stand",
    "стойка": "stand",
    "стойки": "stands",
    "флаг": "flag",
    "рама": "frame",
    "авенджер": "avenger",
    "манфротто": "manfrotto",
    "мэтьюс": "matthews",
}


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
        return image_rendition_url(obj.main_image, RENTAL_MAIN_IMAGE_RENDITION)


class RentalItemDetailSerializer(RentalItemListSerializer):
    gallery = serializers.SerializerMethodField()
    attributes = RentalAttributeValueSerializer(source="attribute_values", many=True)

    class Meta(RentalItemListSerializer.Meta):
        fields = RentalItemListSerializer.Meta.fields + [
            "description",
            "detail_description",
            "seo_title",
            "seo_description",
            "gallery",
            "attributes",
        ]

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
            .filter(category__is_active=True)
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
        if search := params.get("search"):
            queryset = queryset.filter(build_search_query(search))
        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return RentalItemDetailSerializer
        return RentalItemListSerializer


def build_search_query(search):
    query = Q()
    for variant in search_variants(search):
        query |= (
            Q(title__icontains=variant)
            | Q(slug__icontains=variant)
            | Q(short_description__icontains=variant)
            | Q(search_aliases__icontains=variant)
            | Q(description__icontains=variant)
            | Q(detail_description__icontains=variant)
            | Q(category__title__icontains=variant)
            | Q(attribute_values__value_text__icontains=variant)
            | Q(attribute_values__value_choice__icontains=variant)
        )
    return query


def search_variants(search):
    normalized = " ".join(str(search).strip().split())
    if not normalized:
        return []

    variants = {
        normalized,
        normalized.lower(),
        normalized.translate(EN_TO_RU_LAYOUT),
        normalized.translate(RU_TO_EN_LAYOUT),
        transliterate_ru_to_latin(normalized),
    }
    lowered = normalized.lower()
    for latin, russian in LATIN_TO_RU_HINTS.items():
        if latin in lowered:
            variants.add(lowered.replace(latin, russian))
            variants.add(russian)
    for russian, latin in RU_TO_LATIN_HINTS.items():
        if russian in lowered:
            variants.add(lowered.replace(russian, latin))
            variants.add(latin)
    return [variant for variant in variants if variant]


def transliterate_ru_to_latin(value):
    return "".join(RU_TO_LATIN.get(char.lower(), char.lower()) for char in value)
