from rest_framework import serializers

from picker.models import Product, QuizSubmission


class ProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "slug",
            "name",
            "type",
            "roles",
            "scores",
            "summary",
            "description",
            "pros",
            "cons",
            "best_for",
            "not_for",
            "extra_gear",
            "budget_tier",
            "image",
            "is_active",
        ]

    def get_image(self, obj):
        request = self.context.get("request")

        if not obj.image:
            return None

        if request:
            return request.build_absolute_uri(obj.image.url)

        return obj.image.url


class QuizSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizSubmission
        fields = "__all__"


class QuizSubmitSerializer(serializers.Serializer):
    experience = serializers.CharField()
    play_style = serializers.CharField()
    priority = serializers.CharField()
    budget = serializers.CharField()
    maintenance = serializers.CharField()
    weight = serializers.CharField()
    simple_start = serializers.CharField()