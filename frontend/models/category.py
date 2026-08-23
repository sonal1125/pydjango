from django.db import models
from django.template.defaultfilters import slugify    # new
from django.urls import reverse


class Meta:
    app_label="frontend"

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=255, null=False, unique=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children"
    )
    slug = models.SlugField(unique=True)

#static method to retrieve all the categories from the database.
    @staticmethod
    def get_all_categories():
        return Category.objects.all()

#to return the name of the category when it's converted to a string.
    def __str__(self):
        return self.name

    @property
    def has_children(self):
        return self.children.exists()
    
    def get_absolute_url(self):
        return reverse("product_list", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)
