from .models import Sport

def sports_list(request):
    return {'sports': Sport.objects.all()}
