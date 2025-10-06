from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('services/', views.services, name='services'),
    path('products/', views.products, name='products'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('become-a-dealer/', views.become_a_dealer, name='become_a_dealer'),
    path('lizing/', views.lizing, name='lizing'),
    path('news/', views.news, name='news'),
    path('news/<int:new_id>/', views.new_detail, name='new_detail'),
    path('dealers/', views.dealers, name='dealers'),
    path('jobs/', views.jobs, name='jobs'),
]