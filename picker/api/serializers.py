from rest_framework import serializers

from picker.data.quiz_questions import QUIZ_QUESTIONS
from picker.models import Product, QuizSubmission


def _question_choices(question_id):
    for question in QUIZ_QUESTIONS:
        if question["id"] == question_id:
            return [
                (option["value"], option["label"])
                for option in question["options"]
            ]

    return []


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
    experience = serializers.ChoiceField(
        choices=_question_choices("experience"),
    )
    product_goal = serializers.ChoiceField(
        choices=_question_choices("product_goal"),
    )
    play_style = serializers.ChoiceField(
        choices=_question_choices("play_style"),
    )
    play_role = serializers.ChoiceField(
        choices=_question_choices("play_role"),
    )
    priority = serializers.ChoiceField(
        choices=_question_choices("priority"),
    )
    budget = serializers.ChoiceField(
        choices=_question_choices("budget"),
    )
    maintenance = serializers.ChoiceField(
        choices=_question_choices("maintenance"),
    )
    tuning = serializers.ChoiceField(
        choices=_question_choices("tuning"),
    )
    weight = serializers.ChoiceField(
        choices=_question_choices("weight"),
    )
    weather = serializers.ChoiceField(
        choices=_question_choices("weather"),
    )
    extra_gear = serializers.ChoiceField(
        choices=_question_choices("extra_gear"),
    )
    simple_start = serializers.ChoiceField(
        choices=_question_choices("simple_start"),
    )
