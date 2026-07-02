from django.urls import path

from .views import (
    ProductListAPIView,
    ProductDetailAPIView,
    QuizQuestionsAPIView,
    QuizSubmitAPIView,
    SubmissionDetailAPIView,
    FiltersAPIView,
    HealthAPIView, CompareProductsAPIView,
)

urlpatterns = [
    path(
        "products/compare/",
        CompareProductsAPIView.as_view(),
        name="products-compare",
    ),

    path(
        "products/",
        ProductListAPIView.as_view(),
        name="product-list",
    ),

    path(
        "products/<slug:slug>/",
        ProductDetailAPIView.as_view(),
        name="product-detail",
    ),

    path(
        "quiz/questions/",
        QuizQuestionsAPIView.as_view(),
        name="quiz-questions",
    ),

    path(
        "quiz/submit/",
        QuizSubmitAPIView.as_view(),
        name="quiz-submit",
    ),

    path(
        "submissions/<int:pk>/",
        SubmissionDetailAPIView.as_view(),
        name="submission-detail",
    ),

    path(
        "meta/filters/",
        FiltersAPIView.as_view(),
        name="filters",
    ),

    path(
        "health/",
        HealthAPIView.as_view(),
        name="health",
    ),
]