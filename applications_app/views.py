from django.http import HttpResponse


def index(request):
    return HttpResponse("<h1>applications_app ✅</h1><p>Apply / Accept / Reject — OK</p>")
