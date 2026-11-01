from django.urls import path

from . import views

app_name = "estimator"

urlpatterns = [
    path("api/estimate/", views.estimate_api, name="estimate_api"),
    path("api/immigration/", views.immigration_api, name="immigration_api"),
]
