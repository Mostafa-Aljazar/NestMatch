from django.http import HttpResponse


def index(request):
    return HttpResponse("<h1>agreements_app ✅</h1><p>AI Agreements / PDF Download — OK</p>")
