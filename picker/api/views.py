from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics

from picker.models import Product, QuizSubmission
from picker.services.scoring import MissingScoresError, score_products

from .serializers import (
    ProductSerializer,
    QuizSubmitSerializer,
)
from ..data.quiz_questions import QUIZ_QUESTIONS


class ProductListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    allowed_orderings = {
        "name",
        "-name",
        "type",
        "-type",
        "budget_tier",
        "-budget_tier",
        "created_at",
        "-created_at",
    }

    def get_queryset(self):
        queryset = Product.objects.all()

        product_type = self.request.query_params.get("type")
        role = self.request.query_params.get("role")
        budget = self.request.query_params.get("budget")
        search = self.request.query_params.get("search")
        ordering = self.request.query_params.get("ordering")

        if product_type:
            queryset = queryset.filter(type=product_type)

        if budget:
            queryset = queryset.filter(budget_tier=budget)

        if search:
            queryset = queryset.filter(
                name__icontains=search
            )

        if ordering in self.allowed_orderings:
            queryset = queryset.order_by(ordering)

        if role:
            queryset = [
                product
                for product in queryset
                if role in (product.roles or [])
            ]

        return queryset


class ProductDetailAPIView(generics.RetrieveAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    lookup_field = "slug"


class QuizSubmitAPIView(APIView):
    def post(self, request):
        serializer = QuizSubmitSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        answers = serializer.validated_data

        products = Product.objects.all()

        try:
            results = score_products(
                products=products,
                answers=answers,
                top_n=3,
            )
        except MissingScoresError as exc:
            return Response(
                {
                    "detail": "Product scoring data is incomplete.",
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response_results = []

        for item in results:
            product = item["product"]

            response_results.append({
                "slug": product.slug,
                "name": product.name,
                "type": product.type,
                "summary": product.summary,
                "image": (
                    request.build_absolute_uri(product.image.url)
                    if product.image
                    else None
                ),
                "score": item["score"],
                "match_percent": item["match_percent"],
            })

        submission = QuizSubmission.objects.create(
            answers=answers,
            results=response_results,
        )

        return Response(
            {
                "submission_id": submission.id,
                "results": response_results,
            },
            status=status.HTTP_200_OK,
        )


class QuizQuestionsAPIView(APIView):
    def get(self, request):
        return Response(
            {
                "questions": QUIZ_QUESTIONS
            }
        )


class SubmissionDetailAPIView(APIView):
    def get(self, request, pk):
        submission = get_object_or_404(
            QuizSubmission,
            pk=pk,
        )

        return Response(
            {
                "id": submission.id,
                "answers": submission.answers,
                "results": submission.results,
                "created_at": submission.created_at,
            }
        )


class FiltersAPIView(APIView):
    def get(self, request):
        return Response(
            {
                "types": [
                    "AEG",
                    "GBBR",
                    "HPA",
                    "Spring",
                    "GBB",
                ],
                "budgets": [
                    "low",
                    "medium",
                    "high",
                ],
                "roles": [
                    "cqb",
                    "forest",
                    "field",
                    "milsim",
                    "assault",
                    "sniper",
                    "support",
                ],
            }
        )


class HealthAPIView(APIView):
    def get(self, request):
        return Response(
            {
                "status": "ok"
            }
        )


class CompareProductsAPIView(APIView):

    def get(self, request):

        slugs = request.GET.get("slugs", "")

        slugs = [
            slug.strip()
            for slug in slugs.split(",")
            if slug.strip()
        ]

        products = Product.objects.filter(
            slug__in=slugs,
        )

        serializer = ProductSerializer(
            products,
            many=True,
            context={"request": request},
        )

        return Response(
            {
                "products": serializer.data
            }
        )
