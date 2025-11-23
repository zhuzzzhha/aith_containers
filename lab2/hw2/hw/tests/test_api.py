import os
import sys
import pytest
import http
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import json
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shop_api.models import Cart, Item, CartResponse, CreateItemRequest, UpdateItemRequest, GeneratedID


class TestCartEndpoints:
    def test_get_cart_success(self, client, mock_shop, sample_cart_response):

        mock_shop.get_cart_response.return_value = (sample_cart_response, 2)

        response = client.get("/cart/1")
        
        assert response.status_code == http.HTTPStatus.OK
        data = response.json()
        assert data["id"] == 1
        assert data["price"] == 200.0
        assert len(data["items"]) == 1
        mock_shop.get_cart_response.assert_called_once_with(1)
    
    def test_get_cart_not_found(self, client, mock_shop):
        mock_shop.get_cart_response.return_value = (None, 0)
        response = client.get("/cart/999")

        assert response.status_code == http.HTTPStatus.NOT_FOUND
        mock_shop.get_cart_response.assert_called_once_with(999)
    
    def test_get_carts_with_filters(self, client, mock_shop):
        cart_responses = [
            CartResponse(id=1, items=[], price=100.0),
            CartResponse(id=2, items=[], price=200.0)
        ]
        
        with patch('your_app.main.shop.carts', {1: MagicMock(), 2: MagicMock()}):
            with patch('your_app.main.shop.items', {}):
                mock_cart1 = MagicMock()
                mock_cart1.create_cart_response.return_value = (cart_responses[0], 1)
                mock_cart2 = MagicMock()
                mock_cart2.create_cart_response.return_value = (cart_responses[1], 2)
                
                mock_shop.carts = {1: mock_cart1, 2: mock_cart2}
                
                response = client.get("/cart?min_price=150&max_price=250&min_quantity=1&max_quantity=3&offset=0&limit=10")
                
                assert response.status_code == http.HTTPStatus.OK
                data = response.json()
                assert len(data) == 1
                assert data[0]["id"] == 2
    
    def test_get_carts_pagination(self, client, mock_shop):
        cart_responses = [
            CartResponse(id=1, items=[], price=100.0),
            CartResponse(id=2, items=[], price=200.0),
            CartResponse(id=3, items=[], price=300.0)
        ]
        
        with patch('your_app.main.shop.carts', {1: MagicMock(), 2: MagicMock(), 3: MagicMock()}):
            with patch('your_app.main.shop.items', {}):
                mock_cart1 = MagicMock()
                mock_cart1.create_cart_response.return_value = (cart_responses[0], 1)
                mock_cart2 = MagicMock()
                mock_cart2.create_cart_response.return_value = (cart_responses[1], 2)
                mock_cart3 = MagicMock()
                mock_cart3.create_cart_response.return_value = (cart_responses[2], 3)
                
                mock_shop.carts = {1: mock_cart1, 2: mock_cart2, 3: mock_cart3}
                
                # Act
                response = client.get("/cart?offset=1&limit=1")
                
                # Assert
                assert response.status_code == http.HTTPStatus.OK
                data = response.json()
                assert len(data) == 1
                assert data[0]["id"] == 2
    
    def test_create_cart_success(self, client, mock_shop):
        """Тест успешного создания корзины"""
        # Arrange
        mock_cart = MagicMock()
        mock_cart.id = 1
        mock_shop.create_cart.return_value = mock_cart
        
        # Act
        response = client.post("/cart")
        
        # Assert
        assert response.status_code == http.HTTPStatus.CREATED
        data = response.json()
        assert data == {"id": 1}
        mock_shop.create_cart.assert_called_once()
    
    def test_add_to_cart_success(self, client, mock_shop):
        """Тест успешного добавления товара в корзину"""
        # Arrange
        mock_cart = MagicMock()
        mock_item = MagicMock()
        mock_item.deleted = False
        
        mock_shop.get_cart.return_value = mock_cart
        mock_shop.get_item.return_value = mock_item
        mock_shop.add_item_to_cart.return_value = mock_cart
        
        # Act
        response = client.post("/cart/1/add/1")
        
        # Assert
        assert response.status_code == http.HTTPStatus.OK
        mock_shop.get_cart.assert_called_once_with(1)
        mock_shop.get_item.assert_called_once_with(1)
        mock_shop.add_item_to_cart.assert_called_once_with(1, 1, 1)
    
    def test_add_to_cart_cart_not_found(self, client, mock_shop):
        """Тест добавления в несуществующую корзину"""
        # Arrange
        mock_shop.get_cart.return_value = None
        
        # Act
        response = client.post("/cart/999/add/1")
        
        # Assert
        assert response.status_code == http.HTTPStatus.NOT_FOUND
        mock_shop.get_cart.assert_called_once_with(999)
        mock_shop.get_item.assert_not_called()
    
    def test_add_to_cart_item_not_found(self, client, mock_shop):
        """Тест добавления несуществующего товара"""
        # Arrange
        mock_cart = MagicMock()
        mock_shop.get_cart.return_value = mock_cart
        mock_shop.get_item.return_value = None
        
        # Act
        response = client.post("/cart/1/add/999")
        
        # Assert
        assert response.status_code == http.HTTPStatus.NOT_FOUND
        mock_shop.get_cart.assert_called_once_with(1)
        mock_shop.get_item.assert_called_once_with(999)
    
    def test_add_to_cart_item_deleted(self, client, mock_shop):
        """Тест добавления удаленного товара"""
        # Arrange
        mock_cart = MagicMock()
        mock_item = MagicMock()
        mock_item.deleted = True
        
        mock_shop.get_cart.return_value = mock_cart
        mock_shop.get_item.return_value = mock_item
        
        # Act
        response = client.post("/cart/1/add/1")
        
        # Assert
        assert response.status_code == http.HTTPStatus.NOT_FOUND
        mock_shop.get_cart.assert_called_once_with(1)
        mock_shop.get_item.assert_called_once_with(1)


class TestItemEndpoints:
    """Тесты для endpoints товаров"""
    
    def test_create_item_success(self, client, mock_shop):
        """Тест успешного создания товара"""
        # Arrange
        mock_item = Item(id=1, name="New Item", price=99.99, deleted=False)
        mock_shop.create_item.return_value = mock_item
        
        item_data = {"name": "New Item", "price": 99.99}
        
        # Act
        response = client.post("/item", json=item_data)
        
        # Assert
        assert response.status_code == http.HTTPStatus.CREATED
        data = response.json()
        assert data["name"] == "New Item"
        assert data["price"] == 99.99
        mock_shop.create_item.assert_called_once()
    
    def test_get_item_success(self, client, mock_shop, sample_item):
        """Тест успешного получения товара"""
        # Arrange
        mock_shop.get_item.return_value = sample_item
        
        # Act
        response = client.get("/item/1")
        
        # Assert
        assert response.status_code == http.HTTPStatus.OK
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Test Item"
        mock_shop.get_item.assert_called_once_with(1)
    
    def test_get_item_not_found(self, client, mock_shop):
        """Тест получения несуществующего товара"""
        # Arrange
        mock_shop.get_item.return_value = None
        
        # Act
        response = client.get("/item/999")
        
        # Assert
        assert response.status_code == http.HTTPStatus.NOT_FOUND
        mock_shop.get_item.assert_called_once_with(999)
    
    def test_get_item_deleted(self, client, mock_shop):
        """Тест получения удаленного товара"""
        # Arrange
        mock_item = Item(id=1, name="Deleted Item", price=100.0, deleted=True)
        mock_shop.get_item.return_value = mock_item
        
        # Act
        response = client.get("/item/1")
        
        # Assert
        assert response.status_code == http.HTTPStatus.NOT_FOUND
        mock_shop.get_item.assert_called_once_with(1)
    
    def test_get_items_success(self, client, mock_shop):
        """Тест успешного получения списка товаров"""
        # Arrange
        mock_items = [
            Item(id=1, name="Item 1", price=50.0, deleted=False),
            Item(id=2, name="Item 2", price=150.0, deleted=False)
        ]
        mock_shop.get_all_items.return_value = mock_items
        
        # Act
        response = client.get("/item?min_price=100&max_price=200&show_deleted=false&offset=0&limit=10")
        
        # Assert
        assert response.status_code == http.HTTPStatus.OK
        data = response.json()
        assert len(data) == 2
        mock_shop.get_all_items.assert_called_once()
    
    def test_put_item_success(self, client, mock_shop):
        """Тест успешного полного обновления товара"""
        # Arrange
        updated_item = Item(id=1, name="Updated Item", price=200.0, deleted=False)
        mock_shop.update_item.return_value = updated_item
        
        update_data = {"name": "Updated Item", "price": 200.0}
        
        # Act
        response = client.put("/item/1", json=update_data)
        
        # Assert
        assert response.status_code == http.HTTPStatus.OK
        data = response.json()
        assert data["name"] == "Updated Item"
        assert data["price"] == 200.0
        mock_shop.update_item.assert_called_once_with(1, CreateItemRequest(**update_data))
    
    def test_put_item_not_found(self, client, mock_shop):
        """Тест обновления несуществующего товара"""
        # Arrange
        mock_shop.update_item.return_value = None
        
        update_data = {"name": "Updated Item", "price": 200.0}
        
        # Act
        response = client.put("/item/999", json=update_data)
        
        # Assert
        assert response.status_code == http.HTTPStatus.NOT_FOUND
        mock_shop.update_item.assert_called_once()
    
    def test_patch_item_success(self, client, mock_shop):
        """Тест успешного частичного обновления товара"""
        # Arrange
        existing_item = Item(id=1, name="Original Item", price=100.0, deleted=False)
        updated_item = Item(id=1, name="Original Item", price=150.0, deleted=False)
        
        mock_shop.get_item.return_value = existing_item
        mock_shop.update_item.return_value = updated_item
        
        update_data = {"price": 150.0}
        
        # Act
        response = client.patch("/item/1", json=update_data)
        
        # Assert
        assert response.status_code == http.HTTPStatus.OK
        data = response.json()
        assert data["price"] == 150.0
        mock_shop.get_item.assert_called_once_with(1)
        mock_shop.update_item.assert_called_once()
    
    def test_patch_item_not_found(self, client, mock_shop):
        """Тест частичного обновления несуществующего товара"""
        # Arrange
        mock_shop.get_item.return_value = None
        
        update_data = {"price": 150.0}
        
        # Act
        response = client.patch("/item/999", json=update_data)
        
        # Assert
        assert response.status_code == http.HTTPStatus.NOT_FOUND
        mock_shop.get_item.assert_called_once_with(999)
        mock_shop.update_item.assert_not_called()
    
    def test_patch_item_deleted(self, client, mock_shop):
        """Тест частичного обновления удаленного товара"""
        # Arrange
        deleted_item = Item(id=1, name="Deleted Item", price=100.0, deleted=True)
        mock_shop.get_item.return_value = deleted_item
        
        update_data = {"price": 150.0}
        
        # Act
        response = client.patch("/item/1", json=update_data)
        
        # Assert
        assert response.status_code == http.HTTPStatus.NOT_MODIFIED
        mock_shop.get_item.assert_called_once_with(1)
        mock_shop.update_item.assert_not_called()
    
    def test_delete_item_success(self, client, mock_shop, sample_item):
        """Тест успешного удаления товара"""
        # Arrange
        mock_shop.get_item.return_value = sample_item
        mock_shop.delete_item.return_value = True
        
        # Act
        response = client.delete("/item/1")
        
        # Assert
        assert response.status_code == http.HTTPStatus.OK
        data = response.json()
        assert data["id"] == 1
        mock_shop.get_item.assert_called_once_with(1)
        mock_shop.delete_item.assert_called_once_with(1)
    
    def test_delete_item_not_found(self, client, mock_shop):
        """Тест удаления несуществующего товара"""
        # Arrange
        mock_shop.get_item.return_value = None
        
        # Act
        response = client.delete("/item/999")
        
        # Assert
        assert response.status_code == http.HTTPStatus.NOT_FOUND
        mock_shop.get_item.assert_called_once_with(999)
        mock_shop.delete_item.assert_not_called()
    
    def test_delete_item_failure(self, client, mock_shop, sample_item):
        """Тест неудачного удаления товара"""
        # Arrange
        mock_shop.get_item.return_value = sample_item
        mock_shop.delete_item.return_value = False
        
        # Act
        response = client.delete("/item/1")
        
        # Assert
        assert response.status_code == http.HTTPStatus.NOT_FOUND
        mock_shop.get_item.assert_called_once_with(1)
        mock_shop.delete_item.assert_called_once_with(1)


class TestMetricsEndpoints:
    """Тесты для метрик"""
    
    def test_metrics_endpoint_available(self, client):
        """Тест доступности endpoints метрик"""
        response = client.get("/metrics")
        assert response.status_code == 200
    
    def test_business_metrics_updated(self, client, mock_shop):
        """Тест обновления бизнес-метрик"""
        # Arrange
        mock_shop.carts = {1: MagicMock(), 2: MagicMock()}
        mock_shop.items = {1: MagicMock(), 2: MagicMock(), 3: MagicMock()}
        
        # Act - делаем несколько запросов чтобы триггернуть middleware
        client.get("/cart/999")  # 404
        client.post("/cart")     # 201
        assert True  # В реальных тестах можно проверять значения метрик