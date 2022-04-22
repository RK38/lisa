from django.contrib import admin

from .models import *
# Register your models here.

@admin.register(Administration)
class AdministrationAdmin(admin.ModelAdmin):
    list_display=["nom", "mode_test", "debut", "fin", "url"]
    list_editable=["mode_test", "debut", "fin", "url"]

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display=["email", "valide", "cle_choisie", "is_staff", "admin_emails", "admin_stats"]
    list_search=['email']

    def save_model(self, request, obj, form, change):
        actuel=User.objects.get(pk=obj.pk)
        nouvellement_valide=obj.valide and not actuel.valide
        super().save_model(request, obj, form, change)
        if nouvellement_valide:
            obj.send_mail_validation()

@admin.register(Anonyme)
class AnonymeAdmin(admin.ModelAdmin):
    list_display=["hash", ]

@admin.register(LogDeconnexion)
class LogDeconnexionAdmin(admin.ModelAdmin):
    list_display=["user", "date", "code"]
