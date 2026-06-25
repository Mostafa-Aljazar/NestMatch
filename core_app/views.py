from django.http import HttpResponse


def index(request):
    return HttpResponse("<h1>core_app ✅</h1><p>Landing Page — OK</p>")
