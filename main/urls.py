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
    path('api/log-js-error/', views.log_js_error, name='log_js_error'),
    path('test-utm/', TemplateView.as_view(template_name='test-utm.html'), name='test_utm'),
    
    # ========== DASHBOARD ==========
    path('admin/dashboard/', views.dashboard_view, name='admin_dashboard'),
    path('admin/dashboard/api/data/', views.dashboard_api_data, name='dashboard_api_data'),
    path('admin/dashboard/export/excel/', views.dashboard_export_excel, name='dashboard_export_excel'),
    path('admin/dashboard/export/word/', views.dashboard_export_word, name='dashboard_export_word'),
]