from django.http import HttpResponse


def index(request):
    return HttpResponse("<h1>accounts_app ✅</h1><p>Login / Register / Profile — OK</p>")
