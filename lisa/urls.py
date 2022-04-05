"""lisa URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from accueil import views as a_views
from sondage import views as s_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('django.contrib.auth.urls')),
    path('', a_views.Accueil.as_view(), name="accueil"),
    path('attente_validation', TemplateView.as_view(template_name = "utilisateurs/attente_validation.html"),name="attente_validation"),
    path('inscription', a_views.Inscription.as_view(), name="inscription"),
    path('deconnexion', a_views.Deconnexion.as_view(), name="deconnexion"),
    path("cle_secrete", a_views.Phrase.as_view(), name="phrase"),
    path("connecte_anonyme", a_views.ConnecteAnonyme.as_view(), name="connecte_anonyme"),
    path("validation", a_views.Validation.as_view(), name="validation"),
    path("createadmin", a_views.CreateAdmin.as_view(), name="create_admin"),
    path("sondage", TemplateView.as_view(template_name="sondage/sondage.html"), name="sondage"),
    path("etape/<int:numero>", s_views.EtapeView.as_view(), name="etape"),
    path("fin", TemplateView.as_view(template_name="sondage/fin.html"), name="fin"),
    path("resultats", TemplateView.as_view(template_name="sondage/resultats.html"), name="resultats"),
    path('pages/', include('django.contrib.flatpages.urls')),
    ]
