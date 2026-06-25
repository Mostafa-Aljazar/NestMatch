from django.http import HttpResponse


def index(request):
    return HttpResponse("<h1>dashboard_app ✅</h1><p>Poster Dashboard / Seeker Applications / Admin Panel — OK</p>")
