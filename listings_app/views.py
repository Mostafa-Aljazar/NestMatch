from django.http import HttpResponse


def index(request):
    return HttpResponse("<h1>listings_app ✅</h1><p>Room Listings / Post a Room — OK</p>")
