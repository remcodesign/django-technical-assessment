from django.contrib import admin
from django.urls import include, path

urlpatterns =[
    path("polls/", include("polls.urls")),
    path("api/polls/", include("polls.api_urls")),
    path("admin/", admin.site.urls),
]
