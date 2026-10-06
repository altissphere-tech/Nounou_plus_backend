"""
Tests de l'app services.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_liste_des_services_accessible_sans_connexion():
    response = APIClient().get(reverse("services-list"))
    assert response.status_code == status.HTTP_200_OK
    slugs = [service["slug"] for service in response.data]
    assert slugs == ["cuisine", "menage", "nounou"]
