from django.db import models
from .category import Category 
from .seller import Seller
from django.utils.text import slugify

class Meta:
    app_label="frontend"

class Products(models.Model): 
	name = models.CharField(max_length=255) 
	price = models.IntegerField(default=0)
	stock_quantity = models.PositiveIntegerField(
    blank=True,
    null=True,
    help_text="Leave empty for unlimited / non-fixed stock."
    )
	slug = models.SlugField(max_length=255, blank=True, null=False, unique=True)
	category = models.ForeignKey(Category, on_delete=models.CASCADE, default=1, related_name="productss") 
	description = models.TextField(default='', blank=True, null=True) 
	seller = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name="products")

	@staticmethod
	def get_products_by_id(ids): 
		return Products.objects.filter(id__in=ids) 

	@staticmethod
	def get_all_products(): 
		return Products.objects.all() 

	@staticmethod
	def get_all_products_by_categoryid(category_id): 
		if category_id: 
			return Products.objects.filter(category=category_id) 
		else: 
			return Products.get_all_products() 

    #to return the name of the product when it's converted to a string.
	#The method name should be double underscore, not single:
	def __str__(self):
		return self.name

	def save(self, *args, **kwargs):
		if not self.slug:
			base_slug = slugify(self.name)
			slug = base_slug
			counter = 1
			while Products.objects.filter(slug=slug).exclude(pk=self.pk).exists():
				slug = f"{base_slug}-{counter}"
				counter += 1
			self.slug = slug
		super().save(*args, **kwargs)

	@property
	def primary_image(self):
		return self.media.filter(
			media_type="image"
			).order_by("order", "id").first()