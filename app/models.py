from app import db

# Création du modèle de la base de données, cela permet ensuite de faire appel aux objets
# présents dans le modèle pour faire des requêtes.
class Metadata_STAB_ISSW(db.Model):
    ID = db.Column(db.Text, primary_key=True, unique=True)
    Titre = db.Column(db.Text)
    Auteurs = db.Column(db.Text)
    keywords = db.Column(db.Text)
