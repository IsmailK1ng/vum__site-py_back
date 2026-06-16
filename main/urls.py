from django.urls import path
from django.views.generic import TemplateView
from . import views


urlpatterns = [
    path('', views.index, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('services/', views.services, name='services'),
    path('products/', views.products, name='products'),
    path('products/<slug:product_id>/', views.product_detail, name='product_detail'),
    path('become-a-dealer/', views.become_a_dealer, name='become_a_dealer'),
    path('lizing/', views.lizing, name='lizing'),
    path('news/', views.news, name='news'),
    path('news/<slug:slug>/', views.news_detail, name='news_detail'),
    path('dealers/', views.dealers, name='dealers'),
    path('jobs/', views.jobs, name='jobs'),
    path('faq/', views.faq, name='faq'),
    path('team/', views.team, name='team'),
    path('api/log-js-error/', views.log_js_error, name='log_js_error'),

    # ========== ДИЛЕРСКИЙ МАГАЗИН ==========
    path('dealer/login/', views.dealer_login, name='dealer_login'),
    path('dealer/logout/', views.dealer_logout, name='dealer_logout'),
    path('dealer/', views.dealer_shop, name='dealer_shop'),
    path('dealer/part/<int:part_id>/', views.dealer_part_detail, name='dealer_part_detail'),
    path('dealer/cart/', views.dealer_cart_view, name='dealer_cart'),
    path('dealer/api/cart-parts/', views.dealer_cart_api, name='dealer_cart_api'),
    path('dealer/change-password/', views.dealer_change_password, name='dealer_change_password'),

    # ========== DASHBOARD ==========
    path('admin/dashboard/', views.dashboard_view, name='admin_dashboard'),
    path('admin/dashboard/api/data/', views.dashboard_api_data, name='dashboard_api_data'),
    path('admin/dashboard/export/excel/', views.dashboard_export_excel, name='dashboard_export_excel'),
    path('admin/dashboard/export/word/', views.dashboard_export_word, name='dashboard_export_word'),
]