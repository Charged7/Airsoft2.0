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


def _role_tag_for_slug(slug):
    if slug in SUPPORT_ROLE_SLUGS:
        return "support"

    if slug in PRECISION_ROLE_SLUGS:
        return "sniper"

    return "assault"


def sync_semantic_role_tags(apps, schema_editor):
    Product = apps.get_model("picker", "Product")

    for product in Product.objects.all():
        roles = product.roles if isinstance(product.roles, list) else []
        role_tag = _role_tag_for_slug(product.slug)

        if role_tag in roles:
            continue

        product.roles = [*roles, role_tag]
        product.save(update_fields=["roles"])


class Migration(migrations.Migration):

    dependencies = [
        ("picker", "0005_calibrate_product_scores"),
    ]

    operations = [
        migrations.RunPython(
            sync_semantic_role_tags,
            migrations.RunPython.noop,
        ),
    ]
