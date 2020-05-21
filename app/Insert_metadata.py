# Importation du package sqlite3 et csv
import sqlite3
import csv

# Connexion à la base de données déjà existante.
connexion = sqlite3.connect('metadata.db')

# on instancie un curseur avec la méthode .cursor(),
# on stocke le curseur dans la variable c.
c = connexion.cursor()

# Ouverture en mode lecture d'un fichier au format csv,
# on récupère le fichier à partir de son chemin absolu,
# on ouvre de fichier en mode lecture dans la variable csv_f.
with open('/home/max5452/Bureau/ShipStabResearchApp/Elasticsearch_APP/app/Base_metadata_STAB_ISSW.csv', 'r') as csv_f:
    # On parse le fichier au moyen de la méthode DictReader.
    # La méthode .DictReader prend 2 paramètres: le fichier à parser et le type de délimiteur employé.
    # DictReader permet de considérer le fichier csv comme un dictionnaire,
    # on stocke ces informations dans la variable source.
    source = csv.DictReader(csv_f, delimiter=',')

    # Pour chaque ligne du présente dans source, on va récupérer les valeurs associées aux clefs de
    #dictionnaires (ces clefs sont les entêtes de colonnes du fichier csv originel.
    to_db = [(i['ID'], i['Title'], i['Authors'], i['STAB/ISSW'],
              i['year'], i['session n°'], i['paper'],
              i['volume'], i['page'], i['Session'],
              i['keywords'], i['Producteur'], i['Catégorie du producteur'],
              i['Pays'], i['Abstract']
              )
             for i in source]
# Insertion des données dans la table Metadata.
# Pour ne pas répéter l'étape pour chaque ligne,
# on utilise la méthode .executemany.
c.executemany('''INSERT INTO Metadata_STAB_ISSW 
(
 ID, Titre, Auteurs, STAB_ISSW,
 year, session, paper,
 volume, page, Sessions,
 keywords, producteur, catégorie_prod,
 pays, abstract
 )
 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', to_db)

# Sauvegarde des modifications.
connexion.commit()

# On referme la connexion à la base de données.
connexion.close()

