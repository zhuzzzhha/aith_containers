import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Generator

from ..shop_api.main import app
from ..shop_api.models import Cart, Item


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Создаем event loop для тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_item():
    return Item(id=1, name="Test Item", price=100.0, deleted=False)


@pytest.fixture
def sample_cart():
    return Cart(id=1, items={1: 2})


@pytest.fixture
def sample_cart_response():
    return {
        "id": 1,
        "items": [{"id": 1, "name": "Test Item", "price": 100.0, "quantity": 2}],
        "price": 200.0
    }


@pytest.fixture
def mock_shop():
    """Фикстура для мока магазина"""
    with patch('shop_api.main.shop') as mock_shop:
        mock_shop.get_cart_response = MagicMock()
        mock_shop.get_cart = MagicMock()
        mock_shop.create_cart = MagicMock()
        mock_shop.get_item = MagicMock()
        mock_shop.add_item_to_cart = MagicMock()
        mock_shop.create_item = MagicMock()
        mock_shop.get_all_items = MagicMock()
        mock_shop.update_item = MagicMock()
        mock_shop.delete_item = MagicMock()
        
        mock_shop.carts = {}
        mock_shop.items = {}
        
        yield mock_shop