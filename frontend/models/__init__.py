from .category import Category
from .products import Products
from .articles import Articles
from .seller import Seller
from .customer import Customer
from .orders import Order
from .productDeleteOTP import ProductDeleteOTP
from .products import ProductImage

__all__ = [
    'Category',
    'Products',
    'ProductImage', #this table or model in products model file
    'Articles',
    'Seller',
    'Customer',    
    'Order',
    'ProductDeleteOTP',
]
