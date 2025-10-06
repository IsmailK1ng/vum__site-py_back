from django.conf import settings
from django.shortcuts import redirect
from django.utils import translation

from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, 'main/index.html')

def about(request):
    return render(request, 'main/about.html')

def contact(request):
    return render(request, 'main/contact.html')

def services(request):
    return render(request, 'main/services.html')

def products(request):
    return render(request, 'main/products.html')

def become_a_dealer(request):
    return render(request, 'main/become_a_dealer.html')

def lizing(request):
    return render(request, 'main/lizing.html')

def news(request):
    return render(request, 'main/news.html')

def dealers(request):
    return render(request, 'main/dealers.html')

def product_detail(request, product_id):
    # Logic to fetch product details based on product_id
    return render(request, 'main/product_detail.html', {'product_id': product_id})

def jobs(request):
    return render(request, 'main/jobs.html')

def news_detail(request, news_id):
    # Logic to fetch news details based on news_id
    return render(request, 'main/news_detail.html', {'news_id': news_id})

def set_language_get(request):
    lang = request.GET.get("language")
    if lang in dict(settings.LANGUAGES):
        translation.activate(lang)
        request.session[translation.LANGUAGE_SESSION_KEY] = lang
    return redirect(request.META.get("HTTP_REFERER", "/"))