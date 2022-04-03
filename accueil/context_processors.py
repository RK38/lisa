from .models import Administration

def administration(request):
    """Place dans le contexte les informations d'administration"""
    administration, created=Administration.objects.get_or_create(pk=1)
    return {"administration": administration}
