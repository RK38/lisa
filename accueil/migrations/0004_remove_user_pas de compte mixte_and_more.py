# Generated by Django 4.0.3 on 2022-04-22 09:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accueil', '0003_user_admin_emails_user_admin_stats'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='user',
            name='pas de compte mixte',
        ),
        migrations.AddConstraint(
            model_name='user',
            constraint=models.CheckConstraint(check=models.Q(models.Q(('admin_emails', False), ('admin_stats', False), ('is_staff', False)), models.Q(('cle_choisie', False), ('valide', False)), _connector='OR'), name='pas de compte mixte'),
        ),
    ]
