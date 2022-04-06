from django.core.management.base import BaseCommand, CommandError
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model

User=get_user_model()

# La commande manage.py deconnexion_auto doit être lancée régulièrement
class Command(BaseCommand):
    help = "Lance la déconnexion automatique des utilisateurs distraits"

    def handle(self, *args, **options):
        sessions = Session.objects.filter(expire_date__gte=timezone.now()) # sessions en cours
        uid_list = []
        for session in sessions:
            data = session.get_decoded()
            uid_list.append(data.get('_auth_user_id', None)) # liste des utilisateurs connectés
        users=User.objects.exclude(id__in=uid_list).exclude(anonyme=None)
        for user in users:
            if user.anonyme!=None: # vérifions que le statut n'a pas changé
                user.deconnecte_anonyme()
