from django.core.management.base import BaseCommand, CommandError
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model

User=get_user_model()

def get_all_logged_out_users():
    # Query all non-expired sessions
    # use timezone.now() instead of datetime.now() in latest versions of Django
    sessions = Session.objects.filter(expire_date__lt=timezone.now())
    uid_list = []

    # Build a list of user ids from that query
    for session in sessions:
        data = session.get_decoded()
        uid_list.append(data.get('_auth_user_id', None))

    # Query all logged out users based on id list
    return User.objects.filter(id__in=uid_list)

# La commande manage.py deconnexion_auto doit être lancée régulièrement
class Command(BaseCommand):
    help = "Lance la déconnexion automatique des utilisateurs distraits"

    def handle(self, *args, **options):
        users=get_all_logged_out_users().exclude(anonyme=None)
        for user in users:
            if user.anonyme: # vérifions que le statut n'a pas changé
                user.deconnecte_anonyme()
