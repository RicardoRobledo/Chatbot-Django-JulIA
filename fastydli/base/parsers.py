from pydantic import BaseModel


__author__ = 'Ricardo'
__version__ = '1.0'


class ProductFormatter(BaseModel):
    product: str
    quantity: int


class OrderFormatter(BaseModel):
    products: list[ProductFormatter]
