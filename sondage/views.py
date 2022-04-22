from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.contrib.auth.mixins import UserPassesTestMixin
from django import forms
from django.contrib.auth import get_user_model
User=get_user_model()
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from .models import Etape, Option, ReponseOption, Commentaire, CasesACocher
from accueil.models import get_administration, Anonyme


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
        if administration.etat==administration.OUVERT:
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

class ResultatView(generic.TemplateView):
    template_name="sondage/resultats.html"

    def get(self, request, *args, **kwargs):
        administration=get_administration()
        user=request.user
        if user.is_authenticated and (user.admin_stats or (user.cle_choisie and administration.clos)):
            return HttpResponseRedirect(reverse("statistiques"))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context=super().get_context_data(*args, **kwargs)
        context["nombre_anonymes"]=Anonyme.objects.all().count()
        return context

class StatistiqueView(LoginRequiredMixin, UserPassesTestMixin, generic.TemplateView):
    template_name="sondage/statistiques.html"

    def test_func(self):
        user=self.request.user
        administration=get_administration()
        return user.admin_stats or (user.cle_choisie and administration.clos)

    def get_context_data(self, *args, **kwargs):
        context=super().get_context_data(*args, **kwargs)
        context["nombre_anonymes"]=Anonyme.objects.all().count()
        context["etapes"]=Etape.objects.all()
        for etape in context["etapes"]:
            etape.casesacochers_s=CasesACocher.objects.filter(etape=etape)
            for casesacocher in etape.casesacochers_s:
                casesacocher.options_s=Option.objects.filter(casesacocher=casesacocher)
                for option in casesacocher.options_s:
                    option.nombre=ReponseOption.objects.filter(options=option).count()
        return context

def ajaxEffectif(request):
    casesacocher=CasesACocher.objects.get(id=request.GET.get("id_casesacocher"))
    id_options=request.GET.get('id_options') or []
    if id_options:
        id_options=[int(k) for k in id_options.rstrip(";").split(";")]
    anonymes=Anonyme.objects.all()
    for id_option in id_options:
        anonymes=anonymes.filter(reponseoption__options__id=id_option)
    toutes=anonymes.count()
    au_moins_une=Anonyme.objects.filter(reponseoption__options__id__in=id_options).distinct().count()
    return JsonResponse({'toutes':toutes, 'au_moins_une': au_moins_une})

class CommentaireView(LoginRequiredMixin, UserPassesTestMixin, generic.TemplateView):
    template_name="sondage/commentaires.html"

    def test_func(self):
        user=self.request.user
        return user.admin_stats

    def get_context_data(self, *args, **kwargs):
        context=super().get_context_data(*args, **kwargs)
        commentaires=Commentaire.objects.exclude(commentaire="")
        anonymes=Anonyme.objects.filter(commentaire__in=commentaires).distinct()
        context["anonymes"]=anonymes
        for anonyme in anonymes:
            anonyme.commentaires=Commentaire.objects.filter(anonyme=anonyme).exclude(commentaire="")
        return context
