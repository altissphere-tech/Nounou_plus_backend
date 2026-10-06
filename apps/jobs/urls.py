"""
Routes de l'app jobs.
Montées sous le préfixe /api/jobs/ dans config/urls.py.
"""
from django.urls import path

from .views import JobDetailView, JobInterestView, JobListCreateView, MyJobsView

urlpatterns = [
    path("", JobListCreateView.as_view(), name="jobs-list"),
    path("mine/", MyJobsView.as_view(), name="jobs-mine"),
    path("<int:pk>/", JobDetailView.as_view(), name="jobs-detail"),
    path("<int:pk>/interest/", JobInterestView.as_view(), name="jobs-interest"),
]
