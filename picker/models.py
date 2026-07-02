from django.db import models


class Product(models.Model):
    TYPE_CHOICES = [
        ("AEG", "AEG"),
        ("GBBR", "GBBR"),
        ("HPA", "HPA"),
        ("Spring", "Spring"),
        ("GBB", "GBB"),
    ]
    BUDGET_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    roles = models.JSONField(default=list)
    scores = models.JSONField(default=dict)
    summary = models.TextField()
    description = models.TextField()
    pros = models.JSONField(default=list)
    cons = models.JSONField(default=list)
    best_for = models.JSONField(default=list)
    not_for = models.JSONField(default=list)
    extra_gear = models.JSONField(default=list)
    budget_tier = models.CharField(max_length=10, choices=BUDGET_CHOICES)
    image = models.ImageField(upload_to="products/", blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class QuizSubmission(models.Model):
    answers = models.JSONField()
    results = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
