from django.core.management.base import BaseCommand
from django.core.files import File
from frontend.models.products import Products
import os


class Command(BaseCommand):
    help = "Upload existing local product images to Cloudinary"

    def handle(self, *args, **kwargs):
        uploaded = 0
        skipped = 0

        for product in Products.objects.all():

            if not product.image:
                continue

            # Skip if already on Cloudinary
            if "res.cloudinary.com" in product.image.url:
                self.stdout.write(
                    self.style.WARNING(f"Skipped: {product.name} (already on Cloudinary)")
                )
                skipped += 1
                continue

            image_path = product.image.path

            if not os.path.exists(image_path):
                self.stdout.write(
                    self.style.ERROR(f"Missing file: {image_path}")
                )
                continue

            with open(image_path, "rb") as f:
                product.image.save(
                    os.path.basename(image_path),
                    File(f),
                    save=True
                )

            uploaded += 1

            self.stdout.write(
                self.style.SUCCESS(f"Uploaded: {product.name}")
            )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Finished! Uploaded={uploaded}  Skipped={skipped}"
            )
        )