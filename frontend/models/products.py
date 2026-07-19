from django.db import models
from .category import Category 
from .seller import Seller

class Meta:
    app_label="frontend"

class Products(models.Model): 
	name = models.CharField(max_length=255) 
	price = models.IntegerField(default=0) 
	category = models.ForeignKey(Category, on_delete=models.CASCADE, default=1, related_name="productss") 
	description = models.TextField(default='', blank=True, null=True) 
	seller = models.ForeignKey(Seller, on_delete=models.CASCADE, default=1)
	image = models.ImageField(upload_to='uploads/products/', blank=True, null=True) 
	""" image1 = models.ImageField(upload_to='uploads/products/', blank=True, null=True) 
	image2 = models.ImageField(upload_to='uploads/products/', blank=True, null=True) 
	image3 = models.ImageField(upload_to='uploads/products/', blank=True, null=True) 
	image4 = models.ImageField(upload_to='uploads/products/', blank=True, null=True)  
	"""

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
	
	@property
	def image_url(self):
		if self.image:
			return self.image.url
		return '/static/images/default.jpg'
	
	""" def get_all_images(self):
		return [img for img in [self.image, self.image1, self.image2, self.image3, self.image4] if img] """
	

class ProductImage(models.Model):
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='uploads/products/')
    alt_text = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Image for {self.product.name}"