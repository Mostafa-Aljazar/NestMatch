from django.http import HttpResponse
from django.shortcuts import render

def index(request):
    return render(request, 'core_app/landing.html')


#def index(request):
#   return HttpResponse("<h1>core_app ✅</h1><p>Landing Page — OK</p>")
