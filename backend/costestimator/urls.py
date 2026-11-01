from django.urls import include, path

urlpatterns = [
    path("", include("estimator.urls")),
]
