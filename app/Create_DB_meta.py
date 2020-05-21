# Importation de la librairie sqlite3
import sqlite3

# connexion à la base de données metadata.db
# à l'aide de la méthode .connect
# on stocke cette connexion dans la variable connexion
connexion = sqlite3.connect('metadata.db')

# on instancie un curseur avec la méthode .cursor(),
# on stocke le curseur dans la variable c.
c = connexion.cursor()

# création de la table Metada avec la méthode .execute.
c. execute('''CREATE TABLE IF NOT EXISTS Metadata_STAB_ISSW (
ID text,
Titre text,
Auteurs text,
STAB_ISSW text,
year integer,
session integer,
paper integer,
volume integer,
page text,
Sessions text,
keywords text,
producteur text,
catégorie_prod text,
pays text,
abstract text
)
''')

# sauvegarde des modifications précédentes avec la méthode .commit()
connexion.commit()

# fermeture de la connexion à la base de données avec la méthode .close()
connexion.close()