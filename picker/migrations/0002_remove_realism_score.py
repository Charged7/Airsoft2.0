from django.db import migrations


def remove_realism_score(apps, schema_editor):
    Product = apps.get_model("picker", "Product")

    for product in Product.objects.all():
        scores = product.scores or {}

        if "realism" not in scores:
            continue

        scores.pop("realism", None)
        product.scores = scores
        product.save(update_fields=["scores"])


def restore_realism_score(apps, schema_editor):
    Product = apps.get_model("picker", "Product")

    for product in Product.objects.all():
        scores = product.scores or {}

        if "realism" in scores:
            continue

        scores["realism"] = 7
        product.scores = scores
        product.save(update_fields=["scores"])


class Migration(migrations.Migration):

    dependencies = [
        ("picker", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            remove_realism_score,
            restore_realism_score,
        ),
    ]
