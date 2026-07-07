from django.core.management.base import BaseCommand

from picker.models import Product
from picker.data.product_catalog import PRODUCTS


class Command(BaseCommand):
    help = "Seed products database"

    def handle(self, *args, **kwargs):

        created_count = 0
        updated_count = 0

        for item in PRODUCTS:

            product, created = Product.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "name": item["name"],
                    "type": item["type"],
                    "roles": item["roles"],
                    "scores": item["scores"],
                    "summary": item["summary"],
                    "description": item.get("description", ""),
                    "pros": item.get("pros", []),
                    "cons": item.get("cons", []),
                    "best_for": item.get("best_for", []),
                    "not_for": item.get("not_for", []),
                    "extra_gear": item.get("extra_gear", []),
                    "budget_tier": item["budget_tier"],
                },
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Created: {created_count}, Updated: {updated_count}"
            )
        )
