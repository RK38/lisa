# Generated by Django 4.0.3 on 2022-04-03 09:04

import accueil.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('email', models.EmailField(max_length=255, unique=True, verbose_name='adresse e-mail')),
                ('alea', models.CharField(default=accueil.models.alea, max_length=15)),
                ('valide', models.BooleanField(default=False)),
                ('cle_choisie', models.BooleanField(default=False)),
            ],
            managers=[
                ('objects', accueil.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Administration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(default='Sondage anonyme', max_length=150)),
                ('debut', models.DateTimeField(blank=True, default=None, null=True)),
                ('fin', models.DateTimeField(blank=True, default=None, null=True)),
                ('url', models.URLField(blank=True, default=None, null=True)),
                ('mode_test', models.BooleanField(default=True)),
                ('avertissement_debut', models.TextField(default='\n<p>Merci de prendre le temps de répondre à ce sondage.\n  Celui-ci est organisé en plusieurs étapes. Pour chacune d\'entre elles, vous trouverez un\n  ou plusieurs jeux de cases à cocher, de boutons radio et, éventuellement, une zone de commentaire libre.\n  Si vous utilisez cette dernière, soyez vigilant à ne pas donner d\'information permettant de vous identifier\n  (sauf s\'il vous est indifférent de l\'être).</p>\n<p>Pour un jeu de cases à cocher, vous pourrez cocher autant de cases que vous le souhaitez.<br>\n  Pour un jeu de boutons radio, vous devrez cocher une et une seule case.\n</p>\n<p>Cliquez sur "Enregistrer" pour enregistrer vos réponses et passer à l\'étape suivante. Cliquez sur "Étape précédente"\n  pour revenir à l\'étape précédente.\n</p>\n<p>Répétons-le, l\'anonymat de vos réponses est garanti. En vous déconnectant,\n  à la fin du sondage, vous supprimerez tout lien entre\nvotre compte nominatif et votre compte anonyme. Celui-ci ne peut, techniquement,\nêtre rétabli que par vous-même lors d\'une connexion ultérieure.</p>\n')),
                ('avertissement_resultats', models.TextField(default='Les résultats seront disponibles sur cette pages dès la fin du sondage.')),
            ],
            options={
                'verbose_name_plural': 'Administration',
            },
        ),
        migrations.CreateModel(
            name='Anonyme',
            fields=[
                ('hash', models.CharField(max_length=10, primary_key=True, serialize=False)),
                ('hash_phrase', models.CharField(blank=True, default=None, max_length=10, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='LogDeconnexion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('code', models.CharField(max_length=10)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='user',
            name='anonyme',
            field=models.OneToOneField(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accueil.anonyme'),
        ),
        migrations.AddField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions'),
        ),
        migrations.AddConstraint(
            model_name='user',
            constraint=models.CheckConstraint(check=models.Q(('is_staff', False), models.Q(('cle_choisie', False), ('valide', False)), _connector='OR'), name='pas de compte mixte'),
        ),
        migrations.AddConstraint(
            model_name='user',
            constraint=models.CheckConstraint(check=models.Q(('cle_choisie', False), ('valide', True), _connector='OR'), name='pas de compte anonyme sans validation'),
        ),
    ]
