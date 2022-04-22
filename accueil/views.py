from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import Group
from django.utils.encoding import force_bytes
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView
from django.core.exceptions import ValidationError
from django import forms
from django.contrib.auth import get_user_model
User=get_user_model()
from django.urls import reverse, reverse_lazy
from django.core.mail import send_mail, send_mass_mail
from django.conf import settings
from django.contrib import messages
from extra_views import ModelFormSetView
from .models import Anonyme, LogDeconnexion, get_administration


class Accueil(generic.View):
    def get(self, request):
        administration=get_administration()
        user=self.request.user
        if not user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        if user.admin_emails:
            return HttpResponseRedirect(reverse('validation'))
        if user.admin_stats:
            return HttpResponseRedirect(reverse('statistiques'))
        if user.is_staff:
            return HttpResponseRedirect('admin/')
        elif not user.valide:
            return HttpResponseRedirect(reverse('attente_validation'))
        elif not user.cle_choisie:
            if administration.ouvert:
                return HttpResponseRedirect(reverse('phrase'))
            if administration.clos:
                return HttpResponse("Le sondage est clos. Vous ne pouvez plus y participer.")
        elif not user.anonyme:
            return HttpResponseRedirect(reverse('connecte_anonyme'))
        return HttpResponseRedirect(reverse('sondage'))


class Deconnexion(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated and self.request.user.anonyme:
            self.request.user.deconnecte_anonyme()
        return super().dispatch(request, *args, **kwargs)

class PhraseForm(forms.Form):
    phrase=forms.CharField(label="Phrase clé", max_length=150, widget=forms.Textarea)
    confirmation=forms.CharField(max_length=150, widget=forms.Textarea)

    def clean(self):
        cd=super().clean()
        if cd['phrase'] != cd['confirmation']:
            raise ValidationError("Les deux phrases ne coïncident pas")
        if len(cd['phrase'])<10:
            raise ValidationError("La phrase doit comporter au moins 10 caractères")
        return cd


class Phrase(UserPassesTestMixin, generic.FormView):
    form_class=PhraseForm
    template_name="utilisateurs/phrase_form.html"

    def test_func(self):
        user=self.request.user
        return user.is_authenticated and user.valide and get_administration().ouvert

    def post(self, request):
        user=request.user
        form=PhraseForm(request.POST)
        if not form.is_valid():
            return self.form_invalid(form)
        anonyme=Anonyme(hash=user.hash(form.cleaned_data["phrase"]), hash_phrase=user.hash_phrase(form.cleaned_data["phrase"]))
        anonyme.save()
        user.cle_choisie=True
        user.anonyme=anonyme
        user.save()
        messages.success(request, f"Votre compte anonyme a bien été créé et vous pouvez maintenant répondre au sondage. Le lien entre votre compte nominatif et votre compte anonyme \
restera établi tant que vous serez connecté. Ce lien sera rompu lors de votre déconnexion. Nul ne sera alors capable de le rétablir excepté vous, par exemple pour terminer de répondre au sondage ou modifier vos réponses, \
à condition de connaître votre phrase clé:\n\n \
{form.cleaned_data['phrase']}\n\n \
Si vous ne l\'avez pas mémorisée, écrite ou enregistrée, faites-le maintenant. En cas d\'oubli, il sera impossible de la retrouver: ")
        Anonyme.melange()
        return HttpResponseRedirect(reverse("accueil"))

class PhraseForm2(forms.Form):
    phrase=forms.CharField(label="Phrase clé", max_length=150, widget=forms.Textarea)

class ConnecteAnonyme(LoginRequiredMixin, generic.FormView):
    form_class=PhraseForm2
    template_name="utilisateurs/connecte_anonyme_form.html"

    def post(self, request):
        form=PhraseForm2(request.POST)
        if not form.is_valid():
            return self.form_invalid(form)
        try:
            anonyme=Anonyme.objects.get(hash=request.user.hash(form.cleaned_data["phrase"]))
        except Anonyme.DoesNotExist:
            form.add_error("phrase", "Cette phrase n'est pas convenable. Attention, chaque détail compte (accents, espaces, ponctuation, ...).")
            return self.form_invalid(form)
        request.user.anonyme=anonyme
        request.user.save()
        anonyme.hash_phrase=request.user.hash_phrase(form.cleaned_data["phrase"])
        anonyme.save()
        return HttpResponseRedirect(reverse("accueil"))


class CreerCompteForm(forms.ModelForm):
    email_confirmation=forms.EmailField(help_text="Veuillez confirmer votre email")

    class Meta:
        model=User
        fields=['email', 'email_confirmation']

    def _get_validation_exclusions(self):
        """Ne pas signaler que l'email possède déjà un compte"""
        exclude=super()._get_validation_exclusions()
        exclude.append('email')
        return exclude

    def clean(self):
        cleaned_data=super().clean()
        email=cleaned_data["email"]
        email_confirmation=cleaned_data["email_confirmation"]
        if email != email_confirmation:
            raise forms.ValidationError("L'email et l'email de confirmation en coïncident pas")
        return cleaned_data

class Inscription(generic.FormView):
    form_class=CreerCompteForm
    template_name="utilisateurs/inscription_form.html"
    success_url=reverse_lazy("attente_validation")


    def form_valid(self, form):
        cd=form.cleaned_data
        email=cd['email']
        if User.objects.filter(email=email).exists():
            user=User.objects.get(email=email)
        # si le compte existe, on ne lève pas d'erreur mais on envoie un message.
            send_mail(
            "Inscription au sondage",
            render_to_string('utilisateurs/mail_compte_deja_existant.txt').format(email=user.email, nom=get_administration().nom),
            settings.DEFAULT_FROM_EMAIL,
            [user.email]
            )
        else:
            user=form.save(commit=False)
            user.set_password(User.objects.make_random_password(10))
            user.save()
            self.object=user
            lien=self.request.build_absolute_uri(reverse('password_reset_confirm',
                    args=(
                        urlsafe_base64_encode(force_bytes(user.pk)),
                        default_token_generator.make_token(user))))
            send_mail(
                f"Inscription {get_administration().nom}",
                render_to_string('utilisateurs/mail_creation_compte.txt').format(nom=get_administration().nom, lien=lien, email=user.email),
                settings.DEFAULT_FROM_EMAIL,
                [user.email]
                )
            # On prévient les superusers de la demande
            texte_avertissement=render_to_string('utilisateurs/mail_avertissement_nouveau_compte.txt').format(
                email=user.email,
                lien=self.request.build_absolute_uri('/validation'))
            mails_avertissement=[]
            for superuser in User.objects.filter(is_staff=True):
                mails_avertissement.append(
                    ["Nouveau compte",
                     texte_avertissement,
                     settings.DEFAULT_FROM_EMAIL,
                     [superuser.email]
                     ])
            send_mass_mail(mails_avertissement)
        messages.success(self.request, "Votre compte a bien été créé ! \
Veuillez maintenant, afin de certifier qu'il s'agit bien de votre adresse email et de choisir votre mot de passe, consulter votre boîte de courrier électronique, \
puis cliquer sur le lien contenu dans le message qui vient de vous être envoyé (vérifiez vos spams si vous ne le recevez pas).")
        return HttpResponseRedirect(self.get_success_url())

class ValidationForm(forms.ModelForm):
    class Meta:
        fields=("email", "valide", "cle_choisie")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs['readonly']=True
        self.fields["email"].disabled=True
        self.fields["cle_choisie"].widget.attrs['readonly']=True
        self.fields["cle_choisie"].disabled=True
        self.fields["cle_choisie"].label="Compte anonyme créé"

class Validation(LoginRequiredMixin, UserPassesTestMixin, ModelFormSetView):
    model=User
    form_class=ValidationForm
    template_name="utilisateurs/validation_formset.html"
    factory_kwargs = {'extra': 0}

    def test_func(self):
        user=self.request.user
        return user.admin_emails

    def get_queryset(self):
        return User.objects.filter(is_staff=False, admin_stats=False, admin_emails=False).order_by("valide")

    def formset_valid(self, formset):
        if formset.has_changed():
            for form in formset:
                if 'valide' in form.changed_data and form.cleaned_data['valide']:
                    user=form.cleaned_data['id']
                    user.send_mail_validation()
        return super().formset_valid(formset)

    def get_context_data(self, *args, **kwargs):
        context=super().get_context_data(*args, **kwargs)
        context["administrateurs_emails"]=User.objects.filter(admin_emails=True)
        context["administrateurs_stats"]=User.objects.filter(admin_stats=True)
        context["administrateurs"]=User.objects.filter(is_staff=True)
        return context

class CreateAdmin(UserPassesTestMixin, generic.CreateView):
    model=User
    fields=["email", "admin_emails", "admin_stats", "is_staff"]
    template_name="utilisateurs/create_admin_form.html"

    def test_func(self):
        user=self.request.user
        return user.is_authenticated and user.is_superuser

    def form_valid(self, form):
        user=form.save(commit=False)
        user.set_password(User.objects.make_random_password(10))
        user.save()
        if user.is_staff:
            admin=Group.objects.get(name="admin")
            user.groups.add(admin)
        return HttpResponseRedirect(reverse("accueil"))
