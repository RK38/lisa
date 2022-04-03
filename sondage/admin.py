from django.contrib import admin
from .models import *


class CasesACocherInline(admin.TabularInline):
    model=CasesACocher
    extra=1

@admin.register(Etape)
class EtapeAdmin(admin.ModelAdmin):
    list_display=["numero", "introduction"]
    list_editable=["introduction"]
    inlines=[CasesACocherInline,]

class OptionInLine(admin.TabularInline):
    model=Option
    extra=1

@admin.register(CasesACocher)
class CasesACocherAdmin(admin.ModelAdmin):
    list_display=["titre", "explicatif", "unique", "ordre"]
    list_editable=["explicatif", "unique", "ordre"]
    list_filter=["etape"]
    inlines=[OptionInLine,]

@admin.register(ReponseOption)
class ReponseOptionAdmin(admin.ModelAdmin):
    list_display=["anonyme"]

@admin.register(Commentaire)
class CommentaireAdmin(admin.ModelAdmin):
    list_display=["etape", "anonyme", "commentaire"]
