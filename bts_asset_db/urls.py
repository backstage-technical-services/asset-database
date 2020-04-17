from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

from . import views

app_name = 'bts_asset_db'
urlpatterns = [
    # ex: 
    path('', views.index, name='index'),
    # ex: records/
    path('records/', views.get_records, name='records'),
    # ex: tests/
    path('tests/', views.get_tests, name='tests'),
    # ex: visual/
    path('visual/', views.visual, name='visual'),
    # ex: visual/search/
    path('visual/search/', views.get_visuals, name='search_visual'),
    # ex: visual/12/note/
    path('visual/<int:vis_id>/note/', views.update_visual_note, name='update_visual_note'),
]
