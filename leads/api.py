from rest_framework import generics, serializers

from leads.models import Lead
from leads.services import create_contact_lead, create_rental_lead
from rental.models import RentalItem


class RentalLeadItemInputSerializer(serializers.Serializer):
    rental_item = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=RentalItem.objects.none(),
    )
    quantity = serializers.IntegerField(min_value=1, default=1)
    comment = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rental_item"].queryset = RentalItem.objects.published().filter(
            is_active=True,
            category__is_active=True,
        )


class LeadCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ["id", "name", "phone", "email", "message"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        return create_contact_lead(**validated_data)


class RentalLeadCreateSerializer(serializers.ModelSerializer):
    items = RentalLeadItemInputSerializer(many=True, write_only=True)

    class Meta:
        model = Lead
        fields = [
            "id",
            "name",
            "phone",
            "email",
            "message",
            "rental_start_date",
            "rental_end_date",
            "items",
        ]
        read_only_fields = ["id"]

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one rental item is required.")
        return value

    def create(self, validated_data):
        items = validated_data.pop("items")
        return create_rental_lead(items=items, **validated_data)


class ContactLeadCreateView(generics.CreateAPIView):
    serializer_class = LeadCreateSerializer


class RentalLeadCreateView(generics.CreateAPIView):
    serializer_class = RentalLeadCreateSerializer
