"""
Core views - Home page and shared views
"""

from django.shortcuts import render


def home(request):
    """
    Home page view - landing page for the VA Benefits Navigator
    """
    context = {
        'page_title': 'Welcome to VA Benefits Navigator',
    }
    return render(request, 'core/home.html', context)
