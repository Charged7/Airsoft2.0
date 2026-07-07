from django.db import migrations


PRECISION_ROLE_SLUGS = {
    "dragunov-svd",
    "hk417-dmr",
    "hk417-gbbr",
    "jg-bar-10",
    "jg-bar10",
    "l96-aws",
    "m110-dmr",
    "m110-gbbr",
    "m14-ebr",
    "m24",
    "m24-sniper",
    "m40a3",
    "m40a5",
    "mk12-spr",
    "silverback-srs",
    "silverback-tac41",
    "sr-25-gbbr",
    "sr25-dmr",
    "sr25-gbbr",
    "ssg96",
    "svd-aeg",
    "tm-vsr10",
    "tokyo-marui-vsr-10",
    "vss-vintorez",
    "well-mb01",
}

SUPPORT_ROLE_SLUGS = {
    "m249-saw",
    "m60",
    "mg42",
    "mk46",
    "mk48",
    "pkp-pecheneg",
    "rpd",
    "rpk-16",
    "rpk-74",
    "stoner-96",
}

UPGRADE_POTENTIAL_BY_SLUG = {
    "aap-01-assassin": 10,
    "ak-aeg": 8,
    "desert-eagle": 3,
    "glock-18c": 7,
    "jg-bar10": 9,
    "m4-aeg": 9,
    "mk18-aeg": 9,
    "mtw-billet": 8,
    "mtw-forged": 8,
    "mtw-tactical": 8,
    "silverback-srs": 9,
    "silverback-tac41": 9,
    "tm-vsr10": 10,
    "well-mb01": 7,
}


def _upgrade_potential_for_product(product):
    if product.slug in UPGRADE_POTENTIAL_BY_SLUG:
        return UPGRADE_POTENTIAL_BY_SLUG[product.slug]

    roles = product.roles if isinstance(product.roles, list) else []

    if product.type == "HPA":
        return 8

    if "sniper" in roles or product.slug in PRECISION_ROLE_SLUGS:
        return 8

    if product.type == "GBBR":
        return 7

    if "support" in roles or product.slug in SUPPORT_ROLE_SLUGS:
        return 6

    if product.type == "GBB":
        return 6

    if product.type == "AEG":
        return 7

    return 5


def add_upgrade_potential_scores(apps, schema_editor):
    Product = apps.get_model("picker", "Product")

    for product in Product.objects.all():
        scores = product.scores if isinstance(product.scores, dict) else {}
        scores["upgrade_potential"] = _upgrade_potential_for_product(product)
        product.scores = scores
        product.save(update_fields=["scores"])


def remove_upgrade_potential_scores(apps, schema_editor):
    Product = apps.get_model("picker", "Product")

    for product in Product.objects.all():
        scores = product.scores if isinstance(product.scores, dict) else {}

        if "upgrade_potential" not in scores:
            continue

        scores.pop("upgrade_potential")
        product.scores = scores
        product.save(update_fields=["scores"])


class Migration(migrations.Migration):

    dependencies = [
        ("picker", "0007_remove_product_is_active"),
    ]

    operations = [
        migrations.RunPython(
            add_upgrade_potential_scores,
            remove_upgrade_potential_scores,
        ),
    ]
