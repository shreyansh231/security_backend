from django.urls import path
from .views import add_project

urlpatterns = [
    path('add-project/', add_project, name='add-project')
]
