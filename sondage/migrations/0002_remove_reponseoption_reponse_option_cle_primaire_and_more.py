# Generated by Django 4.0.3 on 2022-04-05 20:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accueil', '0002_alter_administration_avertissement_debut_and_more'),
        ('sondage', '0001_initial'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='reponseoption',
            name='reponse_option_cle_primaire',
        ),
        migrations.AlterField(
            model_name='reponseoption',
            name='anonyme',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='accueil.anonyme'),
        ),
    ]
