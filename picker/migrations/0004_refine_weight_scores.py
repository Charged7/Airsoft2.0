from django.db import migrations


WEIGHT_SCORE_BY_SLUG = {
    "1911-colt": 9,
    "1911-meu": 9,
    "aap-01-assassin": 10,
    "aap-01c": 10,
    "ak-104-aeg": 7,
    "ak-105-aeg": 7,
    "ak-105-gbbr": 5,
    "ak-12k-aeg": 7,
    "ak-47-aeg": 5,
    "ak-74m-aeg": 6,
    "ak-aeg": 6,
    "aks-74u-aeg": 7,
    "aks-74u-gbbr": 6,
    "arp556-aeg": 8,
    "arp9-aeg": 8,
    "bcm-mcmr-gbbr": 6,
    "cm16-raider": 8,
    "cm16-srxl": 7,
    "cz-p10c": 10,
    "cz-shadow-2": 8,
    "daniel-defense-mk18-gbbr": 6,
    "desert-eagle": 7,
    "dragunov-svd": 4,
    "f2000-aeg": 7,
    "fal-aeg": 4,
    "g36c-aeg": 8,
    "glock-18c": 10,
    "glock-34": 9,
    "glock-45": 10,
    "hk416-aeg": 6,
    "hk417-aeg": 4,
    "hk417-dmr": 4,
    "hk417-gbbr": 4,
    "hk45": 9,
    "jg-bar-10": 8,
    "jg-bar10": 8,
    "kac-sr16-gbbr": 6,
    "kriss-vector": 8,
    "l85a2-aeg": 5,
    "l96-aws": 5,
    "m110-dmr": 4,
    "m110-gbbr": 4,
    "m14-ebr": 2,
    "m24": 5,
    "m24-sniper": 5,
    "m249-saw": 3,
    "m4-aeg": 7,
    "m40a3": 5,
    "m40a5": 5,
    "m60": 2,
    "mcx-virtus-aeg": 6,
    "mg42": 1,
    "mk12-spr": 5,
    "mk18-aeg": 7,
    "mk18-gbbr": 6,
    "mk46": 4,
    "mk48": 2,
    "mp5-aeg": 8,
    "mp5a5": 8,
    "mp5k-aeg": 9,
    "mp5k-pdw": 8,
    "mp5sd6": 7,
    "mp7-aeg": 10,
    "mp7a1": 10,
    "mpx-aeg": 8,
    "mpx-pdw": 9,
    "mtw-billet": 8,
    "mtw-forged": 7,
    "mtw-tactical": 8,
    "mws-m4-gbbr": 6,
    "novritsch-ssp1": 9,
    "novritsch-ssp2": 9,
    "novritsch-ssp5": 8,
    "p90-tr": 8,
    "pkp-pecheneg": 1,
    "polarstar-f2-ak": 6,
    "polarstar-f2-m4": 7,
    "polarstar-kythera-ak": 6,
    "polarstar-kythera-m4": 7,
    "rpd": 3,
    "rpk-16": 4,
    "rpk-74": 4,
    "scar-l-aeg": 6,
    "scorpion-evo-3": 9,
    "sig-m18": 9,
    "sig-mcx-gbbr": 6,
    "sig-p226": 9,
    "sig-p320": 9,
    "silverback-srs": 6,
    "silverback-tac41": 6,
    "sr-25-gbbr": 4,
    "sr25-dmr": 4,
    "sr25-gbbr": 4,
    "ssg96": 5,
    "stoner-96": 4,
    "svd-aeg": 4,
    "tavor-tar-21-aeg": 6,
    "thompson-aeg": 5,
    "tm-vsr10": 8,
    "tokyo-marui-vsr-10": 8,
    "ump45": 8,
    "ump9": 8,
    "usp-compact": 10,
    "vector-aeg": 8,
    "vp9": 10,
    "vss-vintorez": 6,
    "walther-ppq": 10,
    "well-mb01": 5,
    "wolverine-inferno-gen2": 7,
    "wolverine-reaper-ak": 6,
    "wolverine-reaper-m4": 7,
}


def refine_weight_scores(apps, schema_editor):
    Product = apps.get_model("picker", "Product")

    for product in Product.objects.all():
        if product.slug not in WEIGHT_SCORE_BY_SLUG:
            continue

        scores = product.scores or {}
        scores["weight"] = WEIGHT_SCORE_BY_SLUG[product.slug]
        product.scores = scores
        product.save(update_fields=["scores"])


def restore_weight_scores_from_comfort(apps, schema_editor):
    Product = apps.get_model("picker", "Product")

    for product in Product.objects.all():
        scores = product.scores or {}

        if "weight" not in scores:
            continue

        scores["weight"] = scores.get("comfort", scores["weight"])
        product.scores = scores
        product.save(update_fields=["scores"])


class Migration(migrations.Migration):

    dependencies = [
        ("picker", "0003_add_weight_score_and_ergonomics_priority"),
    ]

    operations = [
        migrations.RunPython(
            refine_weight_scores,
            restore_weight_scores_from_comfort,
        ),
    ]
