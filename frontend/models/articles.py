from django.db import models

class Meta:
    app_label="frontend"

class Articles(models.Model): 
	name = models.CharField(max_length=255) 
	description = models.TextField(default='', blank=True, null=True) 
	image = models.ImageField(upload_to='uploads/articles/', blank=True, null=True) 
	flag = models.BooleanField(default=True)

	@staticmethod
	def get_all_articles(): 
		return Articles.objects.all() 

	#to return the name of the product when it's converted to a string.
	def __str__(self):
		return self.name
	
	