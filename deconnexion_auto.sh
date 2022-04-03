#!/bin/bash
# supprime le lien compte nominatif - compte anonyme des utilisateurs dont la session est périmée (oubli de déconnexion)
#source /home/env/bin/activate
python /home/lisa/manage.py deconnexion_auto
#deactivate
