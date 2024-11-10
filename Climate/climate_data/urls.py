from django.urls import path
from . import views

urlpatterns = [
    path('load-data/', views.load_data_from_csv, name='load_data'),
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('search', views.search, name='search'),
    path('home', views.home, name='home_dash'),
    path('temp', views.temp, name='temp'),
    path('heat_maps/', views.heatMaps, name='heat_maps'),
    path('co2', views.co2, name='co2'),
    path('Climaforecast', views.Climaforecast, name='Climaforecast')
]



