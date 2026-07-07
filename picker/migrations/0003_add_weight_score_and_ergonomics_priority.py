from django.db import migrations


def add_weight_score_and_rename_priority(apps, schema_editor):
    Product = apps.get_model("picker", "Product")
    QuizSubmission = apps.get_model("picker", "QuizSubmission")

    for product in Product.objects.all():
        scores = product.scores or {}

        if "weight" not in scores:
            scores["weight"] = scores.get("comfort", 5)
            product.scores = scores
            product.save(update_fields=["scores"])

    for submission in QuizSubmission.objects.all():
        answers = submission.answers or {}

        if answers.get("priority") != "maneuverability":
            continue

        answers["priority"] = "ergonomics"
        submission.answers = answers
        submission.save(update_fields=["answers"])


def remove_weight_score_and_restore_priority(apps, schema_editor):
    Product = apps.get_model("picker", "Product")
    QuizSubmission = apps.get_model("picker", "QuizSubmission")

    for product in Product.objects.all():
        scores = product.scores or {}

        if "weight" not in scores:
            continue

        scores.pop("weight", None)
        product.scores = scores
        product.save(update_fields=["scores"])

    for submission in QuizSubmission.objects.all():
        answers = submission.answers or {}

        if answers.get("priority") != "ergonomics":
            continue

        answers["priority"] = "maneuverability"
        submission.answers = answers
        submission.save(update_fields=["answers"])


class Migration(migrations.Migration):

    dependencies = [
        ("picker", "0002_remove_realism_score"),
    ]

    operations = [
        migrations.RunPython(
            add_weight_score_and_rename_priority,
            remove_weight_score_and_restore_priority,
        ),
    ]
