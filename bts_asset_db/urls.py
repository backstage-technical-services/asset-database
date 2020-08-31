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
    # ex: assets/
    path('assets/', views.asset_search, name='assets'),
    # ex: assets/departments/
    path('assets/departments/', views.get_departments, name='departments'),
    # ex: assets/categories/
    path('assets/categories/', views.get_categories, name='categories'),
    # ex: assets/categories/
    path('assets/subcategories/', views.get_subcategories, name='subcategories'),
    # ex: assets/itemclasses/
    path('assets/itemclasses/', views.get_itemclasses, name='itemclasses'),
    # ex: assets/itemclasses/92/
    path('assets/itemclasses/<int:itemclass_id>/', views.itemclass_info, name='itemclass'),
    # ex: assets/items/120/
    path('assets/items/<int:item_id>/', views.get_item, name='item'),
    # ex: assets/items/test/120/
    path('assets/items/test/<int:item_id>/', views.test_get_item, name='item_test'),
    # ex: tests/
    path('tests/', views.get_tests, name='tests'),
    # ex: visual/
    path('visual/', views.visual, name='visual'),
    # ex: visual/search/
    path('visual/search/', views.get_visuals, name='search_visual'),
    # ex: visual/12/note/
    path('visual/<int:vis_id>/note/', views.update_visual_note, name='update_visual_note'),
]
