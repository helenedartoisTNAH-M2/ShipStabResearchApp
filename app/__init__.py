# Importation des librairies pour gérer les chemins et les requêtes sur les fichiers.
from flask import Flask
from elasticsearch import Elasticsearch
import os
from flask_sqlalchemy import SQLAlchemy


# définition des chemins pour que l'application récupère les templates etc.
chemin_actuel = os.path.dirname(os.path.abspath(__file__))
templates = os.path.join(chemin_actuel, 'templates')
static = os.path.join(chemin_actuel, 'static')
pdf = os.path.dirname('static/PDF_STAB_ISSW')

# creation del'application avec le module flask, on rappelle ce dont l'application à besoin pour fonctionner.
app = Flask(__name__,
            template_folder=templates,
            static_folder=static)

# Configuration de la connexion à la base de données d'indexation des articles.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/max5452/Bureau/ShipStabResearchApp/DB_metadata_csv/metadata.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# On initialise la base de données SQLAlchemy dans l'application au moyen de la variable db.
db = SQLAlchemy(app)

# On initialise la connexion à Elasticsearch dans la variable es,
es = Elasticsearch()

from app import routes