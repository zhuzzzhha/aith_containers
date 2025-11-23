import pytest
from pydantic import ValidationError

from ..shop_api.models import Cart, Item, CartResponse, CreateItemRequest, UpdateItemRequest, GeneratedID


class TestCartModel:
    """Тесты модели Cart"""
    
    def test_cart_creation(self):
        """Тест создания корзины"""
        cart = Cart(id=1, items={1: 2, 2: 3})
        assert cart.id == 1
        assert cart.items == {1: 2, 2: 3}
    
    def test_create_cart_response(self):
        """Тест создания ответа корзины"""
        cart = Cart(id=1, items={1: 2, 2: 1})
        
        items = {
            1: Item(id=1, name="Item1", price=100.0, deleted=False),
            2: Item(id=2, name="Item2", price=50.0, deleted=False)
        }
        
        cart_response, total_quantity = cart.create_cart_response(items)
        
        assert cart_response.id == 1
        assert cart_response.price == 250.0  # 2*100 + 1*50
        assert len(cart_response.items) == 2
        assert total_quantity == 3


class TestItemModels:
    """Тесты моделей товаров"""
    
    def test_update_item_request_optional_fields(self):
        """Тест опциональных полей UpdateItemRequest"""
        # Только имя
        request = UpdateItemRequest(name="New Name")
        assert request.name == "New Name"
        assert request.price is None
        
        # Только цена
        request = UpdateItemRequest(price=150.0)
        assert request.name is None
        assert request.price == 150.0
        
        # Оба поля
        request = UpdateItemRequest(name="New Name", price=200.0)
        assert request.name == "New Name"
        assert request.price == 200.0
    
    def test_generated_id_model(self):
        """Тест модели GeneratedID"""
        generated_id = GeneratedID(id=123)
        assert generated_id.id == 123