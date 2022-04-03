from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.contrib.auth.mixins import UserPassesTestMixin
from django import forms
from django.contrib.auth import get_user_model
User=get_user_model()
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from .models import Etape, ReponseOption, Commentaire
from accueil.models import get_administration


class EtapeForm(forms.Form):
    def __init__(self, etape, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for casesacocher in etape.casesacochers.all():
            options=casesacocher.options.all()
            if not casesacocher.unique:
                self.fields[casesacocher.titre]=forms.ModelMultipleChoiceField(
                    queryset=options,
                    widget=forms.CheckboxSelectMultiple(),
                    required=casesacocher.obligatoire,
                    help_text=casesacocher.explicatif)
            else:
                self.fields[casesacocher.titre]=forms.ModelChoiceField(
                    queryset=options,
                    widget=forms.RadioSelect(),
                    required=casesacocher.obligatoire,
                    help_text=casesacocher.explicatif)
        if etape.commentaire:
            self.fields["commentaire"]=forms.CharField(
                widget=forms.Textarea(),
                label="Commentaire libre",
                required=False)

class EtapeView(UserPassesTestMixin, generic.FormView):
    form_class=EtapeForm
    template_name="sondage/etape_form.html"

    def test_func(self):
        user=self.request.user
        return user.is_authenticated and user.valide and user.anonyme

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        user=request.user
        if user.is_authenticated:
            self.etape=Etape.objects.get(numero=kwargs["numero"])
            self.anonyme=user.anonyme

    def get_success_url(self):
        numero_suivant=self.etape.numero_suivant()
        if numero_suivant:
            return reverse("etape", kwargs={"numero": numero_suivant})
        return reverse("fin")

    def get_form_kwargs(self):
        kwargs=super().get_form_kwargs()
        kwargs["etape"]=self.etape
        return kwargs

    def get_initial(self):
        initial=super().get_initial()
        anonyme=self.anonyme
        reponseoptions=ReponseOption.objects.filter(anonyme=anonyme)
        for casesacocher in self.etape.casesacochers.all():
            reponses=casesacocher.options.filter(reponseoption__in = reponseoptions)
            if casesacocher.unique:
                if reponses:
                    initial.update({casesacocher.titre: reponses[0]})
            else:
                initial.update({casesacocher.titre: reponses})
        commentaire, created=Commentaire.objects.get_or_create(etape=self.etape, anonyme=anonyme)
        initial.update({"commentaire": commentaire.commentaire})
        return initial

    def get_context_data(self, **kwargs):
        context=super().get_context_data(**kwargs)
        context["etape"]=self.etape
        return context

    def form_valid(self, form):
        administration=get_administration()
        cd=form.cleaned_data
        reponseoption, created=ReponseOption.objects.get_or_create(anonyme=self.anonyme)
        etape=self.etape
        if administration.ouvert==administration.OUVERT:
            for casesacocher in etape.casesacochers.all():
                if casesacocher.unique:
                    for option in casesacocher.options.all():
                        if option==cd[casesacocher.titre]:
                            reponseoption.options.add(option)
                        else:
                            reponseoption.options.remove(option)
                else:
                    for option in casesacocher.options.all():
                        if option in cd[casesacocher.titre]:
                            reponseoption.options.add(option)
                        else:
                            reponseoption.options.remove(option)
            if etape.commentaire:
                commentaire=Commentaire.objects.get(etape=etape, anonyme=self.anonyme)
                commentaire.commentaire=cd["commentaire"]
                commentaire.save()
        else:
            messages.error(request, "Votre réponse n'a pas été enregistrée car le sondage est clos")
        return super().form_valid(form)
