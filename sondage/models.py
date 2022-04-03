from django.db import models
from accueil.models import Anonyme

class Etape(models.Model):
    numero=models.PositiveSmallIntegerField()
    introduction=models.TextField(default="", blank=True)
    commentaire=models.BooleanField(default=False) # identique si l'utilisateur pourra laisser un commentaire à cette étape

    class Meta():
        constraints=[models.UniqueConstraint(fields=["numero",], name="numero_etape_unique")]
        ordering=["numero"]
        verbose_name_plural="  Étapes"

    def __str__(self):
        return f"Étape {self.numero}"

    def numero_suivant(self):
        if Etape.objects.filter(numero=self.numero+1):
            return self.numero+1

    def numero_precedent(self):
        if self.numero > 1:
            return self.numero-1


class CasesACocher(models.Model):
    titre=models.CharField(default="", max_length=150)
    explicatif=models.TextField(default="", blank=True)
    obligatoire=models.BooleanField(default=False)
    unique=models.BooleanField(default=False)
    ordre=models.PositiveSmallIntegerField(default=0)
    etape=models.ForeignKey(Etape, related_name="casesacochers", on_delete=models.CASCADE)

    class Meta():
        constraints=[models.UniqueConstraint(fields=["titre", "etape"], name="nom_casesacocher_unique")]
        verbose_name_plural=" Cases à cocher"
        ordering=["ordre", "pk"]

    def __str__(self):
        return self.titre

class Option(models.Model):
    """Option possible pour une case à cocher"""
    option=models.CharField(default="", max_length=300)
    ordre=models.PositiveSmallIntegerField(default=0)
    casesacocher=models.ForeignKey(CasesACocher, on_delete=models.CASCADE, related_name="options")

    class Meta():
        ordering=["casesacocher", "ordre"]

    def __str__(self):
        return self.option

class ReponseOption(models.Model):
    anonyme=models.ForeignKey(Anonyme, on_delete=models.CASCADE)
    options=models.ManyToManyField(Option) # toutes les options auxquelles a été répondu "oui"

    class Meta():
        constraints=[models.UniqueConstraint(fields=["anonyme"], name="reponse_option_cle_primaire")]

class Commentaire(models.Model):
    anonyme=models.ForeignKey(Anonyme, on_delete=models.CASCADE)
    etape=models.ForeignKey(Etape, on_delete=models.CASCADE, related_name="+")
    commentaire=models.TextField(default="")

    class Meta():
        constraints=[models.UniqueConstraint(fields=["etape", "anonyme"], name="commentaire_cle_primaire")]
