from django.core.management.base import BaseCommand
from frontend.models import Products, ProductMedia


class Command(BaseCommand):
    help = "Copy old Products.image into ProductMedia"

    def handle(self, *args, **kwargs):

        created = 0
        skipped = 0

        for product in Products.objects.all():

            if not product.image:
                continue

            exists = ProductMedia.objects.filter(
                product=product,
                file=product.image.name
            ).exists()

            if exists:
                skipped += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipped: {product.name}"
                    )
                )
                continue

            ProductMedia.objects.create(
                product=product,
                file=product.image.name,
                media_type="image",
                order=0,
                alt_text=product.name,
            )

            created += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Copied: {product.name}"
                )
            )

        print()
        print("=" * 40)
        print("Created :", created)
        print("Skipped :", skipped)
        print("=" * 40)