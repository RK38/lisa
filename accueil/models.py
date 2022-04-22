import random, string, hashlib
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.db import models, transaction
from django.contrib.auth.models import AbstractUser, UserManager, AnonymousUser, BaseUserManager

class Administration(models.Model):
    """Informations globales du sondage"""
    TROP_TOT=0
    OUVERT=1
    TROP_TARD=2
    nom=models.CharField(max_length=150, default="Sondage Anonyme") # affiché en haut de chaque page
    debut=models.DateTimeField(default=None, null=True, blank=True)      # début de la période de sondage
    fin=models.DateTimeField(default=None, null=True, blank=True)       # fin de cette période
    url=models.URLField(default=None, null=True, blank=True) # url du site de sondage ; sera indiquée dans les mails
    mode_test=models.BooleanField(default=True)   # affiche un message indiquant que les réponses ne seront pas conservées
    avertissement_debut=models.TextField(default=\
"""
<p>Merci de prendre le temps de répondre à ce sondage.
  Celui-ci est organisé en plusieurs étapes. Pour chacune d'entre elles, vous trouverez un
  ou plusieurs jeux de cases à cocher, de boutons radio et, éventuellement, une zone de commentaire libre.
  Si vous utilisez cette dernière, soyez vigilant à ne pas donner d'information permettant de vous identifier
  (sauf s'il vous est indifférent de l'être).</p>
<p>Pour un jeu de cases à cocher, vous pourrez cocher autant de cases que vous le souhaitez.<br>
  Pour un jeu de boutons radio, vous devrez cocher une et une seule case.
</p>
<p>Cliquez sur "Enregistrer" pour enregistrer vos réponses et passer à l'étape suivante. Cliquez sur "Étape précédente"
  pour revenir à l'étape précédente.
</p>
<p>L'anonymat de vos réponses est garanti. En vous déconnectant,
  à la fin du sondage, vous supprimerez tout lien entre
votre compte nominatif et votre compte anonyme. Celui-ci ne peut, techniquement,
être rétabli que par vous-même lors d'une connexion ultérieure.</p>
""")
    avertissement_resultats=models.TextField(default="Les résultats seront disponibles sur cette pages dès la fin du sondage.")

    class Meta:
        verbose_name_plural="Administration"

    @property
    def etat(self):
        if self.debut and timezone.now() < self.debut:
            return self.TROP_TOT
        if self.fin and timezone.now()>self.fin:
            return self.TROP_TARD
        return self.OUVERT

    @property
    def clos(self):
        return self.etat==self.TROP_TARD

    @property
    def ouvert(self):
        return self.etat==self.OUVERT

def get_administration():
        administration, created=Administration.objects.get_or_create(pk=1)
        return administration

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


def alea():
    letters=string.ascii_uppercase+string.ascii_lowercase+string.digits
    return "".join(random.choice(letters) for i in range(15))

class User(AbstractUser):
    USERNAME_FIELD="email"
    REQUIRED_FIELDS=[]
    username=None
    email=models.EmailField(verbose_name='adresse e-mail', max_length=255, unique=True)
    alea=models.CharField(max_length=15, default=alea) # chaîne aléatoire choisie à la création du compte
    valide=models.BooleanField(default=False)      # indique si le participant a été validé par un administrateur
    cle_choisie=models.BooleanField(default=False) # indique si la phrase clef a été choisie
    anonyme=models.OneToOneField("Anonyme", default=None, null=True, blank=True, on_delete=models.SET_NULL)
    admin_emails=models.BooleanField(default=False) # compte admin ayant accès à la validation des comptes nominatifs
    admin_stats=models.BooleanField(default=False) # compte admin ayant accès aux statistiques durant le sondage
    objects = UserManager()

    class Meta():
        constraints=[
            models.CheckConstraint(check=models.Q(is_staff=False, admin_emails=False, admin_stats=False)|models.Q(cle_choisie=False,valide=False), name="pas de compte mixte"),
            models.CheckConstraint(check=models.Q(cle_choisie=False)|models.Q(valide=True), name="pas de compte anonyme sans validation"),
            ]

    @property
    def admin(self):
        return self.is_staff or self.admin_stats or self.admin_emails

    def hash(self, phrase):
        return hashlib.sha256((phrase+self.alea).encode("UTF-8")).hexdigest()[0:10]

    def hash_phrase(self, phrase):
        return hashlib.sha256(phrase.encode("UTF-8")).hexdigest()[0:10]

    def send_mail_validation(self):
        send_mail(
        "Validation de votre inscription au sondage",
        render_to_string('utilisateurs/validation_inscription.txt', {'site': get_administration().nom, 'url': get_administration().url}),
        settings.DEFAULT_FROM_EMAIL,
        [self.email]
        )

    def send_mail_deconnexion(self):
        send_mail(
        "Ticket de participation au sondage",
        render_to_string('utilisateurs/ticket_participation.txt', {'site': get_administration().nom, 'code': self.anonyme.code}),
        settings.DEFAULT_FROM_EMAIL,
        [self.email],
        )

    def log_deconnexion(self):
        logdeconnexion=LogDeconnexion(user=self, code=self.anonyme.code)
        logdeconnexion.save()

    def deconnecte_anonyme(self):
        self.send_mail_deconnexion()
        self.log_deconnexion()
        self.anonyme.hash_phrase=None
        self.anonyme.save()
        self.anonyme=None
        self.save()


class Anonyme(models.Model):
    """Classe qui sera mise en correspondance avec un User durant sa connexion,
    lorsqu'il aura entré sa phrase clé"""
    hash=models.CharField(max_length=10, primary_key=True) # hash alea + phrase
    hash_phrase=models.CharField(max_length=10, null=True, default=None, blank=True) # hash de la phrase seule. Permet de calculer le code de contrôle, dont la diffusion éventuelle ne compromet pas l'anonymat

    @property
    def code(self):
        if self.hash_phrase==None:
            return ""
        from sondage.models import Option, Commentaire
        chaine=self.hash_phrase
        for option in Option.objects.filter(reponseoption__anonyme=self):
            chaine+=str(option.option)
        for commentaire in Commentaire.objects.filter(anonyme=self):
            chaine+=commentaire.commentaire
        return hashlib.sha256(chaine.encode("UTF-8")).hexdigest()[0:10]

    @staticmethod
    def melange():
        """Sélectionne aléatoirement un anonyme non connecté, le supprime et le réenregistre.
        Il s'agit de prévenir toute tentative de rompre l'anonymat en comparant
        l'ordre dans lequels les comptes nominatifs et anonymes ont été
        enregistrés. Est appelé à chaque enregistrement d'un nouveau compte anonyme."""
        from sondage.models import ReponseOption, Option, Commentaire
        anonymes=Anonyme.objects.filter(user=None)
        if anonymes.exists():
            anonyme=random.choice(anonymes)
            hash=anonyme.hash
            with transaction.atomic():
                if not hasattr(anonyme, "user"):  # prévient le cas -- improbable -- où le participant s'est connecté à ce moment
                    if hasattr(anonyme, "reponseoption"):
                        options=list(anonyme.reponseoption.options.all())
                    else:
                        options= Option.objects.none()
                    commentaires=Commentaire.objects.filter(anonyme=anonyme)
                    liste_commentaires=[(commentaire.etape, commentaire.commentaire) for commentaire in commentaires]
                    anonyme.delete()
                    anonyme=Anonyme(hash=hash) # Le compte anonyme n'étant pas connecté, hash_phrase est actuellement à None
                    anonyme.save()
                    reponseoption=ReponseOption(anonyme=anonyme)
                    reponseoption.save()
                    reponseoption.options.set(options)
                    for item in liste_commentaires:
                        commentaire=Commentaire(anonyme=anonyme, etape=item[0], commentaire=item[1])
                        commentaire.save()



class LogDeconnexion(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    date=models.DateTimeField(auto_now_add=True)
    code=models.CharField(max_length=10) # mémorise le code de contrôle de ce participant ; noter que ce code ne peut être calculé que grâce à la phrase secrète, donc ne permet pas d'identifier le compte anonyme
