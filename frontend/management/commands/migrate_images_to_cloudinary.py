import os

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from frontend.models import Products


class Command(BaseCommand):
    help = "Force upload ALL local product images to Cloudinary"

    def handle(self, *args, **options):

        uploaded = 0
        failed = 0

        for product in Products.objects.all():

            if not product.image:
                continue

            filename = os.path.basename(product.image.name)

            local_path = os.path.join(
                settings.BASE_DIR,
                "media",
                "uploads",
                "products",
                filename,
            )

            if not os.path.exists(local_path):
                self.stdout.write(
                    self.style.WARNING(
                        f"Missing local file: {filename}"
                    )
                )
                failed += 1
                continue

            try:
                with open(local_path, "rb") as f:
                    product.image.save(
                        filename,
                        File(f),
                        save=True
                    )

                uploaded += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Uploaded: {filename}"
                    )
                )

            except Exception as e:
                failed += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"{filename} -> {e}"
                    )
                )

        self.stdout.write("")
        self.stdout.write("=" * 50)
        self.stdout.write(f"Uploaded : {uploaded}")
        self.stdout.write(f"Failed   : {failed}")
        self.stdout.write("=" * 50)