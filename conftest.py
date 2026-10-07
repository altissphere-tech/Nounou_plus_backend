"""Réglages communs aux tests."""
import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def clear_cache():
    """Les compteurs des limites d'essais (en cache) repartent de zéro à chaque test."""
    cache.clear()
    yield
    cache.clear()
