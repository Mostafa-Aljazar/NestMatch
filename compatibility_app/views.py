from django.http import HttpResponse


def index(request):
    return HttpResponse("<h1>compatibility_app ✅</h1><p>AI Compatibility Scoring — OK</p>")
