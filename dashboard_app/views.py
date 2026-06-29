
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def index(request):
    # Later you'll pass real context from other apps
    context = {
        'total_users': 8542,
        'active_listings': 2341,
        'total_applications': 15203,
        'banned_users': 24,
    }
    return render(request, 'dashboard_app/index.html', context)