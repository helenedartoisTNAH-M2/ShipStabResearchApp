from flask import render_template, request
import csv
from app.models import Metadata_STAB_ISSW
from app import es, app


# Les fonctions de recherches simples: par expression et par mot-clef.

# Le résultat de cette fonction s'affichera sur la page d'accueil de l'application.
@app.route("/")
# On compte le nombre de documents présent sur le cluster et on le donne en paramètre de la page d'acceuil.
def nbr_doc():
    """Fonction permettant de compter le nombre de document présent sur le cluster."""
    doc_nbr = es.count(index='stability', doc_type='article', body={"query": {"match_all": {}}})
    return render_template('home.html', response=doc_nbr)


# Définition de la route qui pointera vers la page d'accueil du site.
@app.route("/", methods=["GET", "POST"])
def recherche_simple():
    """Fonction qui va requêter l'ensemble des documents à partir d'une phrase ou expression donnée en input."""
    # q = request.args.get('keyword')
    # on récupère l'input du formulaire dans la variable q.
    q = request.form.get("q")

    # Si l'input n'est pas vide, on lance une recherche Query DSL.
    # On stocke cette recherche dans une variable qu'on affichera ensuite dans la page de résultats.
    # On fait une recherche qui regarde non pas chaque mot séparement
    # mais l'expression complète donnée par l'utilisateur.
    if q is not None:
        resp = es.search(index='stability', doc_type='article',
                         body={"size": 10000, "query": {"match_phrase_prefix": {"texte": q}}})

        # La méthode count permet de compter le nombre de résultat d'une requête Elasticseach. On passe ce résultat
        # comme argument de la template pour l'afficher dans le front end.
        count = es.count(index='stability',
                         body={"query": {"match_phrase_prefix": {"texte": q}}})

        # On stocke dans la variable meta les informations récupérées dans la base de données d'indexation à partir de
        # la liste des ID agrégée par la requête Elasticsearch.
        meta = Metadata_STAB_ISSW.query.filter(
            Metadata_STAB_ISSW.ID.in_([hit["_id"] for hit in resp['hits']['hits']])
        ).all()

        # On créé un dictionnaire vide pour les métadonnées auteurs et titres.
        metadata_auteurs_et_titres = {}

        # Pour chaque résultat obtenu dans meta, on créé une entrée de dictionnaire à l'aide de l'ID
        # puis une clef Titre et une clef Auteurs.
        for chaque_resultat in meta:
            metadata_auteurs_et_titres[chaque_resultat.ID] = {
                "titre": chaque_resultat.Titre,
                "auteur": chaque_resultat.Auteurs,
            }

        # Création de la variable contenant les noms de colonnes pour le fichiers de résultat.
        csv_columns = ['ID', 'Titre', 'Auteurs']
        try:
            # On ouvre un fichier au format csv dans le dossier Results,
            with open('/home/max5452/Bureau/ShipStabResearchApp/Elasticsearch_APP/app/static/Results/' + q + '.csv', 'w') as csvfile:
                # On écrit les noms de colonnes et on définit la virgule comme délimiteur.
                writer = csv.DictWriter(csvfile, fieldnames=csv_columns, delimiter=',')
                writer.writeheader()
                # pour chaque résultat récupérer dans meta, on écrit un dictionnaire contenant ID, Titre et Auteur.
                for chaque_resultat in meta:
                    writer.writerow({'ID': chaque_resultat.ID,
                                     'Titre': chaque_resultat.Titre,
                                     'Auteurs': chaque_resultat.Auteurs})
        # En cas d'erreur lors de l'ouverture/la création du fichier, on affiche une erreur I/O.
        except IOError:
            print("I/O error.")

        # On retourne la template home_result.html avec en argument, la requête, la réponse,
        # le dictionnaire de métadonnées et le résultat de la fonction count.
        return render_template('home_result.html', q=q, response=resp, metadata=metadata_auteurs_et_titres,
                               count=count)
    else:
        return render_template('home.html')


@app.route('/fulltext', methods=["GET", "POST"])
def words_search():
    """Fonction qui recherche un mot donné en input par l'utilisateur."""
    query = request.form.get("query")
    # La requête cherche chaque mot indépendamment des autres mots présents dans la requête.
    # Cela entraine un nombre de résultat plus important qu'une recherche par expression et des scores plus faibles.
    if query is not None:
        query_r = es.search(index='stability', doc_type='article',
                            body={"size": 1000, "query": {"match": {"texte": query}}})

        count = es.count(index='stability', doc_type='article',
                         body={"query": {"match": {"texte": query}}})

        meta = Metadata_STAB_ISSW.query.filter(
            Metadata_STAB_ISSW.ID.in_([hit["_id"] for hit in query_r['hits']['hits']])
        ).all()

        metadata_auteurs_et_titres = {}

        for chaque_resultat in meta:
            metadata_auteurs_et_titres[chaque_resultat.ID] = {
                "titre": chaque_resultat.Titre,
                "auteur": chaque_resultat.Auteurs,
            }

            # Création de la variable contenant les noms de colonnes pour le fichiers de résultat.
            csv_columns = ['ID', 'Titre', 'Auteurs']

            try:
                # On ouvre un fichier au format csv dans le dossier Results,
                with open('/home/max5452/Bureau/ShipStabResearchApp/Elasticsearch_APP/app/static/Results/' + query + '.csv', 'w') as csvfile:
                    # On écrit les noms de colonnes et on définit la virgule comme délimiteur.
                    writer = csv.DictWriter(csvfile, fieldnames=csv_columns, delimiter=',')
                    writer.writeheader()
                    # pour chaque résultat récupérer dans meta, on écrit un dictionnaire contenant ID, Titre et Auteur.
                    for chaque_resultat in meta:
                        writer.writerow({'ID': chaque_resultat.ID,
                                         'Titre': chaque_resultat.Titre,
                                         'Auteurs': chaque_resultat.Auteurs})
            # En cas d'erreur lors de l'ouverture/la création du fichier, on affiche une erreur I/O.
            except IOError:
                print("I/O error.")

        return render_template('home_result.html', q=query, response=query_r, metadata=metadata_auteurs_et_titres,
                               count=count)
    else:
        return render_template('home.html')


# Fonctions de recherches dans les métadonnées des documents.
# On trouve une recherche par titre, auteur, mots_clefs, ID et année de publication.

@app.route("/advancedresearch", methods=["GET", "POST"])
def adv_research():
    """Fonction pour faire des recherches sur les titres principaux des articles."""
    # Récupération des informations du formulaire de recherche avancée titre.
    title = request.form.get("title")
    # Valeur constante du titre dans les fichiers JSON.
    json_title = "\"titleStmt\": {\"title\":"
    if title is not None:
        # On cherche dans les documents JSON la chaine de caractères JSON_TITLE et l'expression donnée par l'utilisateur
        # dans le formulaire. Ces deux éléments peuvent être éloignés au maximum de 35 mots.
        title_r = es.search(index='stability',
                            doc_type='article',
                            body={"size": 1000,
                                  "query": {"match_phrase": {"texte": {"query": json_title + title, "slop": 35}}}})

        count = es.count(index='stability',
                         doc_type='article',
                         body={"query": {"match_phrase": {"texte": {"query": json_title + title, "slop": 35}}}})

        # On intègre au template de sortie les informations à afficher.

        meta = Metadata_STAB_ISSW.query.filter(
            Metadata_STAB_ISSW.ID.in_([hit["_id"] for hit in title_r['hits']['hits']])
        ).all()

        metadata_auteurs_et_titres = {}

        for chaque_resultat in meta:
            metadata_auteurs_et_titres[chaque_resultat.ID] = {
                "titre": chaque_resultat.Titre,
                "auteur": chaque_resultat.Auteurs,
            }

            # Création de la variable contenant les noms de colonnes pour le fichiers de résultat.
            csv_columns = ['ID', 'Titre', 'Auteurs']

            try:
                # On ouvre un fichier au format csv dans le dossier Results,
                with open('/home/max5452/Bureau/ShipStabResearchApp/Elasticsearch_APP/app/static/Results/' + title + '.csv', 'w') as csvfile:
                    # On écrit les noms de colonnes et on définit la virgule comme délimiteur.
                    writer = csv.DictWriter(csvfile, fieldnames=csv_columns, delimiter=',')
                    writer.writeheader()
                    # pour chaque résultat récupérer dans meta, on écrit un dictionnaire contenant ID, Titre et Auteur.
                    for chaque_resultat in meta:
                        writer.writerow({'ID': chaque_resultat.ID,
                                         'Titre': chaque_resultat.Titre,
                                         'Auteurs': chaque_resultat.Auteurs})
            # En cas d'erreur lors de l'ouverture/la création du fichier, on affiche une erreur I/O.
            except IOError:
                print("I/O error.")

        return render_template("meta_result.html", q=title, response=title_r, metadata=metadata_auteurs_et_titres,
                               count=count)
    else:
        return render_template('recherche.html')


@app.route('/author_research', methods=["GET", "POST"])
def author_research():
    """Fonction pour rechercher un auteur d'article."""
    # Récupération de l'input utilisateur dans le formulaire author.
    author = request.form.get("author")
    # Chaîne de caractères précédants toujours les noms et prénoms d'auteurs dans les documents XML et JSON.
    json_author = "\"sourceDesc\": { \"biblStruct\": { \"analytic\": {\"author\": {\"persName\": {"
    # Si l'input n'est pas vide
    if author is not None:
        # On recherche dans les documents la valeur entrée par l'utilisateur.
        # L'écart autorisé entre la clef json_author et le mot recherché est plus restreint (10)
        # car on ne se trouve pas dans de la recherche plein texte.
        # Les éléments de noms d'auteurs sont toujours regroupés dans les métadonnées.
        author_r = es.search(index='stability',
                             doc_type='article',
                             # Le nombre maximum de résultats par auteur est fixé à 100. Peu nombreux sont les auteurs à
                             # avoir publié autant d'article.
                             body={"size": 100,
                                   "query": {
                                       "match_phrase": {"texte": {"query": json_author + author, "slop": 200}}}})

        count = es.count(index='stability',
                         doc_type='article',
                         body={"query": {
                             "match_phrase": {"texte": {"query": json_author + author, "slop": 100}}}})

        meta = Metadata_STAB_ISSW.query.filter(
            Metadata_STAB_ISSW.ID.in_([hit["_id"] for hit in author_r['hits']['hits']])
        ).all()

        metadata_auteurs_et_titres = {}

        for chaque_resultat in meta:
            metadata_auteurs_et_titres[chaque_resultat.ID] = {
                "titre": chaque_resultat.Titre,
                "auteur": chaque_resultat.Auteurs,
            }

            # Création de la variable contenant les noms de colonnes pour le fichiers de résultat.
            csv_columns = ['ID', 'Titre', 'Auteurs']

            try:
                # On ouvre un fichier au format csv dans le dossier Results,
                with open('/home/max5452/Bureau/ShipStabResearchApp/Elasticsearch_APP/app/static/Results/' + author + '.csv', 'w') as csvfile:
                    # On écrit les noms de colonnes et on définit la virgule comme délimiteur.
                    writer = csv.DictWriter(csvfile, fieldnames=csv_columns, delimiter=',')
                    writer.writeheader()
                    # pour chaque résultat récupérer dans meta, on écrit un dictionnaire contenant ID, Titre et Auteur.
                    for chaque_resultat in meta:
                        writer.writerow({'ID': chaque_resultat.ID,
                                         'Titre': chaque_resultat.Titre,
                                         'Auteurs': chaque_resultat.Auteurs})
            # En cas d'erreur lors de l'ouverture/la création du fichier, on affiche une erreur I/O.
            except IOError:
                print("I/O error.")

        return render_template("meta_result.html", q=author, response=author_r, metadata=metadata_auteurs_et_titres,
                               count=count)
    else:
        return render_template('recherche.html')


@app.route('/keyword_research', methods=["GET", "POST"])
def keyword_research():
    """ Fonction de recherche dans les mots-clefs des articles."""
    # Récupération des mots-clefs donnés par l'utilisateur.
    keywords = request.form.get("keywords")
    # La liste des mots clefs des articles est toujours précédée de la chaîne de caractères présente dans json_keywords.
    json_keywords = "\"keywords\": {"
    if keywords is not None:
        # Le slop autorisé est de 20 car la liste des mots_clefs ne connait pas une taille maximale
        # et des expressions peuvent servir de mots-clefs dans certains articles.
        keywords_r = es.search(index='stability',
                               doc_type='article',
                               # Le nombre de résultat par mot-clef peut vite augmenter,
                               # on met donc en place un nombre important de résultats maximum.
                               body={"size": 1000, "query": {
                                   "match_phrase": {"texte": {"query": json_keywords + keywords, "slop": 20}}}})

        count = es.count(index='stability',
                         doc_type='article',
                         body={"query": {
                             "match_phrase": {"texte": {"query": json_keywords + keywords, "slop": 20}}}})

        meta = Metadata_STAB_ISSW.query.filter(
            Metadata_STAB_ISSW.ID.in_([hit["_id"] for hit in keywords_r['hits']['hits']])
        ).all()

        metadata_auteurs_et_titres = {}

        for chaque_resultat in meta:
            metadata_auteurs_et_titres[chaque_resultat.ID] = {
                "titre": chaque_resultat.Titre,
                "auteur": chaque_resultat.Auteurs,
            }

            # Création de la variable contenant les noms de colonnes pour le fichiers de résultat.
            csv_columns = ['ID', 'Titre', 'Auteurs']

            try:
                # On ouvre un fichier au format csv dans le dossier Results,
                with open('/home/max5452/Bureau/ShipStabResearchApp/Elasticsearch_APP/app/static/Results/' + keywords + '.csv', 'w') as csvfile:
                    # On écrit les noms de colonnes et on définit la virgule comme délimiteur.
                    writer = csv.DictWriter(csvfile, fieldnames=csv_columns, delimiter=',')
                    writer.writeheader()
                    # pour chaque résultat récupérer dans meta, on écrit un dictionnaire contenant ID, Titre et Auteur.
                    for chaque_resultat in meta:
                        writer.writerow({'ID': chaque_resultat.ID,
                                         'Titre': chaque_resultat.Titre,
                                         'Auteurs': chaque_resultat.Auteurs})
            # En cas d'erreur lors de l'ouverture/la création du fichier, on affiche une erreur I/O.
            except IOError:
                print("I/O error.")

        return render_template("meta_result.html", q=keywords, response=keywords_r, metadata=metadata_auteurs_et_titres,
                               count=count)
    else:
        return render_template('recherche.html')


@app.route('/id_r', methods=["GET", "POST"])
def get_doc_id():
    """Recherche de document par ID."""
    # On récupère l'ID entré par l'utilisateur.
    identif = request.form.get('id')
    if identif is not None:
        id_r = es.search(index='stability',
                         doc_type='article',
                         # On requête directement le champ '_id'.
                         # Pour plus de facilité dans le traitement de la requête,
                         # on considère l'input utilisateur comme un seul terme (c'est normalement vrai pour les
                         # identifiants de ce projet).
                         body={"query": {"term": {"_id": identif}}})

        count = es.count(index='stability',
                         doc_type='article',
                         body={"query": {"term": {"_id": identif}}})

        meta = Metadata_STAB_ISSW.query.filter(
            Metadata_STAB_ISSW.ID.in_([hit["_id"] for hit in id_r['hits']['hits']])
        ).all()

        metadata_auteurs_et_titres = {}

        for chaque_resultat in meta:
            metadata_auteurs_et_titres[chaque_resultat.ID] = {
                "titre": chaque_resultat.Titre,
                "auteur": chaque_resultat.Auteurs,
                "keywords": chaque_resultat.Keywords,
            }

            # Création de la variable contenant les noms de colonnes pour le fichiers de résultat.
            csv_columns = ['ID', 'Titre', 'Auteurs']

            try:
                # On ouvre un fichier au format csv dans le dossier Results,
                with open('/home/max5452/Bureau/ShipStabResearchApp/Elasticsearch_APP/app/static/Results/' + identif + '.csv', 'w') as csvfile:
                    # On écrit les noms de colonnes et on définit la virgule comme délimiteur.
                    writer = csv.DictWriter(csvfile, fieldnames=csv_columns, delimiter=',')
                    writer.writeheader()
                    # pour chaque résultat récupérer dans meta, on écrit un dictionnaire contenant ID, Titre et Auteur.
                    for chaque_resultat in meta:
                        writer.writerow({'ID': chaque_resultat.ID,
                                         'Titre': chaque_resultat.Titre,
                                         'Auteurs': chaque_resultat.Auteurs})
            # En cas d'erreur lors de l'ouverture/la création du fichier, on affiche une erreur I/O.
            except IOError:
                print("I/O error.")

        return render_template('meta_result.html', q=identif, response=id_r, metadata=metadata_auteurs_et_titres,
                               count=count)
    else:
        return render_template('recherche.html')


@app.route('/year', methods=["GET", "POST"])
def year_re():
    """Recherche de document par date de congré."""
    # On récupère la valeur de l'année entrée par l'utilisateur.
    # Cette valeur doit être composée de 4 signes, 4 chiffres: comment le vérifier?
    year = request.form.get('year')
    if year is not None:
        # On recherche cette valeur au niveau du champs 'date' présent pour chaque document dans ses métadonnées.
        year_r = es.search(index='stability',
                           doc_type='article',
                           body={"size": 100, "query": {"match": {"date": year}}})

        count = es.count(index='stability',
                         doc_type='article',
                         body={"query": {"match": {"date": year}}})

        meta = Metadata_STAB_ISSW.query.filter(
            Metadata_STAB_ISSW.ID.in_([hit["_id"] for hit in year_r['hits']['hits']])
        ).all()

        metadata_auteurs_et_titres = {}

        for chaque_resultat in meta:
            metadata_auteurs_et_titres[chaque_resultat.ID] = {
                "titre": chaque_resultat.Titre,
                "auteur": chaque_resultat.Auteurs,
            }

            # Création de la variable contenant les noms de colonnes pour le fichiers de résultat.
            csv_columns = ['ID', 'Titre', 'Auteurs']

            try:
                # On ouvre un fichier au format csv dans le dossier Results,
                with open('/home/max5452/Bureau/ShipStabResearchApp/Elasticsearch_APP/app/static/Results/' + year + '.csv', 'w') as csvfile:
                    # On écrit les noms de colonnes et on définit la virgule comme délimiteur.
                    writer = csv.DictWriter(csvfile, fieldnames=csv_columns, delimiter=',')
                    writer.writeheader()
                    # pour chaque résultat récupérer dans meta, on écrit un dictionnaire contenant ID, Titre et Auteur.
                    for chaque_resultat in meta:
                        writer.writerow({'ID': chaque_resultat.ID,
                                         'Titre': chaque_resultat.Titre,
                                         'Auteurs': chaque_resultat.Auteurs})
            # En cas d'erreur lors de l'ouverture/la création du fichier, on affiche une erreur I/O.
            except IOError:
                print("I/O error.")

        return render_template('meta_result.html', q=year, response=year_r, metadata=metadata_auteurs_et_titres,
                               count=count)
    else:
        return render_template('recherche.html')


# Fonction de recherche relatives aux organisations.
# Rechercher par nom d'organisation, par type et par pays.

@app.route('/orgName', methods=["GET", "POST"])
def orgname_research():
    """Recherche par non d'organisation."""
    organization = request.form.get('orgName')
    # Les noms d'organisation sont toujours précédés de la balise "orgname". On va donc l'utiliser pour effectuer une
    # requête plus fine dans les documents.
    json_orgname = "\"orgName\": {"
    if organization is not None:
        organization_r = es.search(index='stability',
                                   doc_type='article',
                                   # Certaines recherches telle que "university" présentent de grande chance
                                   # d'apparaître à de nombreuses reprises dans les résultats de noms d'organisation.
                                   # On met donc en place une limite de résultat grande pour aggréger un maximum de
                                   # réponses pertinentes.
                                   body={"size": 1000, "query": {
                                       "match_phrase": {
                                           "texte": {"query": json_orgname + organization, "slop": 10}}}
                                         })

        count = es.count(index='stability',
                         doc_type='article',
                         body={"query": {
                             "match_phrase": {
                                 "texte": {"query": json_orgname + organization, "slop": 10}}}})

        meta = Metadata_STAB_ISSW.query.filter(
            Metadata_STAB_ISSW.ID.in_([hit["_id"] for hit in organization_r['hits']['hits']])
        ).all()

        metadata_auteurs_et_titres = {}

        for chaque_resultat in meta:
            metadata_auteurs_et_titres[chaque_resultat.ID] = {
                "titre": chaque_resultat.Titre,
                "auteur": chaque_resultat.Auteurs,
            }

        # Création de la variable contenant les noms de colonnes pour le fichiers de résultat.
        csv_columns = ['ID', 'Titre', 'Auteurs']

        try:
            # On ouvre un fichier au format csv dans le dossier Results,
            with open('/home/max5452/Bureau/ShipStabResearchApp/Elasticsearch_APP/app/static/Results/' + organization + '.csv', 'w') as csvfile:
                # On écrit les noms de colonnes et on définit la virgule comme délimiteur.
                writer = csv.DictWriter(csvfile, fieldnames=csv_columns, delimiter=',')
                writer.writeheader()
                # pour chaque résultat récupérer dans meta, on écrit un dictionnaire contenant ID, Titre et Auteur.
                for chaque_resultat in meta:
                    writer.writerow({'ID': chaque_resultat.ID,
                                     'Titre': chaque_resultat.Titre,
                                     'Auteurs': chaque_resultat.Auteurs})
        # En cas d'erreur lors de l'ouverture/la création du fichier, on affiche une erreur I/O.
        except IOError:
            print("I/O error.")

        return render_template("meta_result.html", q=organization, response=organization_r,
                               metadata=metadata_auteurs_et_titres, count=count)
    else:
        return render_template('recherche.html')


@app.route('/orgType', methods=["GET", "POST"])
def orgtype_r():
    """Recherche de document en fonction de leur type d'institution."""
    # Récupération de la valeur sélectionnée par l'utilisateur.
    orgtype = request.form.get('orgType')
    json_orgtype = "\"orgName\": {\"@type\":"
    if orgtype is not None:
        orgtype_re = es.search(index='stability',
                               doc_type='article',
                               # On laisse une limite large pour ce type de requête car il y a minimum un type
                               # d'institution par article dans le corpus.
                               # On n'établit pas de slop car il n'y a pas de mots entre la clefs JSON
                               # et le type de l'organisation.
                               body={"size": 1000, "query": {"match_phrase": {"texte": {
                                   "query": json_orgtype + orgtype}}}})

        count = es.count(index='stability',
                         doc_type='article',
                         body={"query": {"match_phrase": {"texte": {
                             "query": json_orgtype + orgtype}}}})

        meta = Metadata_STAB_ISSW.query.filter(
            Metadata_STAB_ISSW.ID.in_([hit["_id"] for hit in orgtype_re['hits']['hits']])
        ).all()

        metadata_auteurs_et_titres = {}

        for chaque_resultat in meta:
            metadata_auteurs_et_titres[chaque_resultat.ID] = {
                "titre": chaque_resultat.Titre,
                "auteur": chaque_resultat.Auteurs,
            }

        # Création de la variable contenant les noms de colonnes pour le fichiers de résultat.
        csv_columns = ['ID', 'Titre', 'Auteurs']

        try:
            # On ouvre un fichier au format csv dans le dossier Results,
            with open('/home/max5452/Bureau/ShipStabResearchApp/Elasticsearch_APP/app/static/Results/' + orgtype + '.csv', 'w') as csvfile:
                # On écrit les noms de colonnes et on définit la virgule comme délimiteur.
                writer = csv.DictWriter(csvfile, fieldnames=csv_columns, delimiter=',')
                writer.writeheader()
                # pour chaque résultat récupérer dans meta, on écrit un dictionnaire contenant ID, Titre et Auteur.
                for chaque_resultat in meta:
                    writer.writerow({'ID': chaque_resultat.ID,
                                     'Titre': chaque_resultat.Titre,
                                     'Auteurs': chaque_resultat.Auteurs})
        # En cas d'erreur lors de l'ouverture/la création du fichier, on affiche une erreur I/O.
        except IOError:
            print("I/O error.")

        return render_template('meta_result.html', q=orgtype, response=orgtype_re, metadata=metadata_auteurs_et_titres,
                               count=count)
    else:
        return render_template('recherche.html')


@app.route('/country', methods=["GET", "POST"])
def country_research():
    """Recherche de document par pays (lié à l'institution de rattachement des auteurs."""
    # On récupère la valeur de country donnée par l'utilisateur.
    country = request.form.get('country')
    # Définition de la chaine de caractères présentes juste avant les mentions de pays dans les métadonnées.
    json_country = "\"country\": {\"@key\":"
    if country is not None:
        country_r = es.search(index='stability',
                              doc_type='article',
                              # Définition d'un nombre large de résultats car les pays sont mentionnées pour chaque
                              # organisation donnée en métadonnées et il y a souvent plusieurs auteurs donc plusieurs
                              # organisations par article.
                              # Je n'autorise pas de slop, il n'y a pas d'autres éléments entre la chaine de caractères
                              # json_country et le pays dans les fichiers XML et JSON.
                              body={"size": 1000,
                                    "query": {"match_phrase": {"texte": {"query": json_country + country}}}})

        count = es.count(index='stability',
                         doc_type='article',
                         body={"query": {"match_phrase": {"texte": {"query": json_country + country}}}})

        meta = Metadata_STAB_ISSW.query.filter(
            Metadata_STAB_ISSW.ID.in_([hit["_id"] for hit in country_r['hits']['hits']])
        ).all()

        metadata_auteurs_et_titres = {}

        for chaque_resultat in meta:
            metadata_auteurs_et_titres[chaque_resultat.ID] = {
                "titre": chaque_resultat.Titre,
                "auteur": chaque_resultat.Auteurs,
            }

        # Création de la variable contenant les noms de colonnes pour le fichiers de résultat.
        csv_columns = ['ID', 'Titre', 'Auteurs']

        try:
            # On ouvre un fichier au format csv dans le dossier Results,
            with open('/home/max5452/Bureau/ShipStabResearchApp/Elasticsearch_APP/app/static/Results/' + country + '.csv', 'w') as csvfile:
                # On écrit les noms de colonnes et on définit la virgule comme délimiteur.
                writer = csv.DictWriter(csvfile, fieldnames=csv_columns, delimiter=',')
                writer.writeheader()
                # pour chaque résultat récupérer dans meta, on écrit un dictionnaire contenant ID, Titre et Auteur.
                for chaque_resultat in meta:
                    writer.writerow({'ID': chaque_resultat.ID,
                                     'Titre': chaque_resultat.Titre,
                                     'Auteurs': chaque_resultat.Auteurs})
        # En cas d'erreur lors de l'ouverture/la création du fichier, on affiche une erreur I/O.
        except IOError:
            print("I/O error.")

        return render_template("meta_result.html", q=country, response=country_r, metadata=metadata_auteurs_et_titres,
                               count=count)
    else:
        return render_template('recherche.html')


# Recherche dans les références et bibliographies des articles.
# Recherche par titre, auteur et date.

@app.route("/bibliographyresearch", methods=["GET", "POST"])
def bibliography_research():
    """Recherche dans les titre présents dans les références des articles."""
    # Récupération des informations du formulaire de recherche avancée "biliography".
    bibliography = request.form.get("bibliography")
    # Clefs json permettant d'accéder aux titres dans la partie bibliographie/référence des articles.
    json_bibliography = "\"monogr\": {\"title\": {"
    if bibliography is not None:
        # On cherche dans les documents JSON la chaine de caractères json_bibliography et l'expression donnée
        # par l'utilisateur dans le formulaire. Ces deux éléments peuvent être éloignés au maximum de 35 mots
        # (35 mots représentant déjà un très long titre).
        bibliography_r = es.search(index='stability',
                                   doc_type='article',
                                   # On donne un grand normbre de résultat pour rester le plus exhaustif possible.
                                   body={"size": 1000,
                                         "query": {"match_phrase": {
                                             "texte": {"query": json_bibliography + bibliography, "slop": 35}}}})

        count = es.count(index='stability',
                         doc_type='article',
                         body={"query": {"match_phrase": {
                             "texte": {"query": json_bibliography + bibliography, "slop": 35}}}})

        meta = Metadata_STAB_ISSW.query.filter(
            Metadata_STAB_ISSW.ID.in_([hit["_id"] for hit in bibliography_r['hits']['hits']])
        ).all()

        metadata_auteurs_et_titres = {}

        for chaque_resultat in meta:
            metadata_auteurs_et_titres[chaque_resultat.ID] = {
                "titre": chaque_resultat.Titre,
                "auteur": chaque_resultat.Auteurs,
            }

        # Création de la variable contenant les noms de colonnes pour le fichiers de résultat.
        csv_columns = ['ID', 'Titre', 'Auteurs']

        try:
            # On ouvre un fichier au format csv dans le dossier Results,
            with open('/Bureau/ShipStabResearchApp/Elasticsearch_APP/app/static/Results/' + bibliography + '.csv', 'w') as csvfile:
                # On écrit les noms de colonnes et on définit la virgule comme délimiteur.
                writer = csv.DictWriter(csvfile, fieldnames=csv_columns, delimiter=',')
                writer.writeheader()
                # pour chaque résultat récupérer dans meta, on écrit un dictionnaire contenant ID, Titre et Auteur.
                for chaque_resultat in meta:
                    writer.writerow({'ID': chaque_resultat.ID,
                                     'Titre': chaque_resultat.Titre,
                                     'Auteurs': chaque_resultat.Auteurs})
        # En cas d'erreur lors de l'ouverture/la création du fichier, on affiche une erreur I/O.
        except IOError:
            print("I/O error.")

        return render_template("meta_result.html", q=bibliography, response=bibliography_r,
                               metadata=metadata_auteurs_et_titres, count=count)
    else:
        return render_template('recherche.html')


@app.route('/author_ref', methods=["GET", "POST"])
def author_ref_research():
    """Recherche dans les auteurs cités en références dans les articles."""
    author_ref = request.form.get("author_ref")
    json_author_ref = "\"@type\": \"references\", \"listBibl\": {\"biblStruct\": [ {"
    # Si l'input n'est pas vide
    if author_ref is not None:
        author_ref_r = es.search(index='stability',
                                 doc_type='article',
                                 # Le nombre maximum de résultats par auteur est fixé à 100.
                                 # Peu nombreux sont les auteurs à avoir publié autant d'article.
                                 body={"size": 100,
                                       "query": {
                                           "match_phrase": {
                                               "texte": {"query": json_author_ref + author_ref, "slop": 500}}}})

        count = es.count(index='stability',
                         doc_type='article',
                         body={"query": {
                             "match_phrase": {
                                 "texte": {"query": json_author_ref + author_ref, "slop": 150}}}})

        meta = Metadata_STAB_ISSW.query.filter(
            Metadata_STAB_ISSW.ID.in_([hit["_id"] for hit in author_ref_r['hits']['hits']])
        ).all()

        metadata_auteurs_et_titres = {}

        for chaque_resultat in meta:
            metadata_auteurs_et_titres[chaque_resultat.ID] = {
                "titre": chaque_resultat.Titre,
                "auteur": chaque_resultat.Auteurs,
            }

        # Création de la variable contenant les noms de colonnes pour le fichiers de résultat.
        csv_columns = ['ID', 'Titre', 'Auteurs']

        try:
            # On ouvre un fichier au format csv dans le dossier Results,
            with open('/home/max5452/Bureau/ShipStabResearchApp/Elasticsearch_APP/app/static/Results/' + author_ref + '.csv', 'w') as csvfile:
                # On écrit les noms de colonnes et on définit la virgule comme délimiteur.
                writer = csv.DictWriter(csvfile, fieldnames=csv_columns, delimiter=',')
                writer.writeheader()
                # pour chaque résultat récupérer dans meta, on écrit un dictionnaire contenant ID, Titre et Auteur.
                for chaque_resultat in meta:
                    writer.writerow({'ID': chaque_resultat.ID,
                                     'Titre': chaque_resultat.Titre,
                                     'Auteurs': chaque_resultat.Auteurs})
        # En cas d'erreur lors de l'ouverture/la création du fichier, on affiche une erreur I/O.
        except IOError:
            print("I/O error.")

        return render_template("meta_result.html", q=author_ref, response=author_ref_r,
                               metadata=metadata_auteurs_et_titres, count=count)
    else:
        return render_template('recherche.html')


# Requête par date dans le texte, cela risque avant tout de donner des résultats dans la bibliographies des articles.
@app.route('/date', methods=["GET", "POST"])
def date_research():
    """Recherche dans les dates des articles présents dans les références."""
    # On récupère la date donnée en input par l'utilisateur.
    date = request.form.get("date")
    json_date = "\"@when\":\""
    if date is not None:
        date_r = es.search(index='stability',
                           doc_type='article',
                           # Les dates peuvent apparaitre fréquemment dans les articles lors de la citation
                           # et des références bibliographiques. On a donc laisssé un grand nombre de résultat par page.
                           body={"size": 1000, "query": {"match": {"texte": json_date + date}}
                                 })

        count = es.count(index='stability',
                         doc_type='article',
                         body={"query": {"match": {"texte": json_date + date}}})

        meta = Metadata_STAB_ISSW.query.filter(
            Metadata_STAB_ISSW.ID.in_([hit["_id"] for hit in date_r['hits']['hits']])
        ).all()

        metadata_auteurs_et_titres = {}

        for chaque_resultat in meta:
            metadata_auteurs_et_titres[chaque_resultat.ID] = {
                "titre": chaque_resultat.Titre,
                "auteur": chaque_resultat.Auteurs,
            }

        # Création de la variable contenant les noms de colonnes pour le fichiers de résultat.
        csv_columns = ['ID', 'Titre', 'Auteurs']

        try:
            # On ouvre un fichier au format csv dans le dossier Results,
            with open('/home/max5452/Bureau/ShipStabResearchApp/Elasticsearch_APP/app/static/Results/' + date + '.csv', 'w') as csvfile:
                # On écrit les noms de colonnes et on définit la virgule comme délimiteur.
                writer = csv.DictWriter(csvfile, fieldnames=csv_columns, delimiter=',')
                writer.writeheader()
                # pour chaque résultat récupérer dans meta, on écrit un dictionnaire contenant ID, Titre et Auteur.
                for chaque_resultat in meta:
                    writer.writerow({'ID': chaque_resultat.ID,
                                     'Titre': chaque_resultat.Titre,
                                     'Auteurs': chaque_resultat.Auteurs})
        # En cas d'erreur lors de l'ouverture/la création du fichier, on affiche une erreur I/O.
        except IOError:
            print("I/O error.")

        return render_template("meta_result.html", q=date, response=date_r, metadata=metadata_auteurs_et_titres,
                               count=count)
    else:
        return render_template('recherche.html')


# Page de documentation de l'application.
@app.route("/doc")
def documentation():
    return render_template('documentation.html')


# Page d'erreurs 404.
@app.route("/404")
def error_404():
    return render_template('404.html'), 404


@app.route("/ISO_3166")
def iso_3166():
    """Lien vers la page contenant la norme ISO 3166 pour utiliser les codes pays dans les recherches."""
    return render_template('ISO_3166.html')


# Page de recherche complexe, dans plusieurs champs du document.

@app.route('/complex_research', methods=["GET", "POST"])
# Fonction permettant d'établir des requêtes sur plusieurs facettes des documents simultanément.
def complex_research():
    """Recherche complexe: on faite des requêtes combinées avec un input texte pouvant correspondre à:
    le corps du texte,
    le titre,
    les titres en références,
    un auteur,
    un auteur en référence,
    un nom d'organisation,
    un mot_clef.
    Mais aussi une requête par date: de congré ou de publication d'article et enfin par type d'organisation."""
    # On récupère les informations du formulaire complex_research: l'input utilisateur
    # et les différentes options cochées.
    text = request.form.get('text')
    date = request.form.get('date')
    title = request.form.get('title')
    title_ref = request.form.get('title_ref')
    author = request.form.get('author')
    author_ref = request.form.get('author_ref')
    ref_date = request.form.get('ref_date')
    orgname = request.form.get('orgname')
    keyword = request.form.get('keyword')
    # L'utilisateur doit donner un texte (des mots-clefs) et une date. S'il n'en donne qu'un, la recherche ne s'effectue pas.
    # Si l'utilisateur a choisi: titre, titre des références, auteurs, auteurs des références, nom d'organisation ou mot_clef
    # on lance la recherche complexe. Si l'utilisateur n'a choisi aucune option de recherche, la requête ne s'effectue pas.
    # Si l'utilisateur n'a coché aucune option, on procède alors à une simple recherche.
    if text is not None and date is not None:
        if title is not None or title_ref is not None or author is not None or author_ref is not None or ref_date is not None or orgname is not None or keyword is not None:
            # La requête doit matcher le texte de l'input de l'utilisateur et peut aggréger les documents qui répondrait aux criètes suivant: la date, la date dans les références,
            # le titre (principal ou dans les références), le nom d'auteur (principal ou dans les références), le nom de l'organisation, les mots-clefs.
            complexsearch = es.search(index='stability',
                                      doc_type='article',
                                      body={"size": 1000, "query": {
                                          "bool": {
                                              "must": {"match_phrase": {"texte": text}},
                                              "should": [
                                                  {"match": {
                                                      "date": date}},
                                                  {"match": {
                                                      "texte": "\"@when\":\"" + date}},
                                                  {"match": {
                                                      "texte": "\"titleStmt\": {\"title\":" + text}},
                                                  {"match": {
                                                      "texte": "\"monogr\": {\"title\": {" + text}},
                                                  {"match": {
                                                      "texte": "\"sourceDesc\": { \"biblStruct\": { \"analytic\": {\"author\": {\"persName\": {" + text}},
                                                  {"match": {
                                                      "texte": "\"@type\": \"references\", \"listBibl\": {\"biblStruct\": [ { \"author\": [" + text}},
                                                  {"match": {
                                                      "texte": "\"orgName\": {" + text}},
                                                  {"match": {
                                                      "texte": "\"keywords\": {" + text}}
                                              ],
                                          }}})

            count = es.count(index='stability',
                             doc_type='article',
                             body={"query": {
                                 "bool": {
                                     "must": {"match_phrase": {"texte": text}},
                                     "should": [
                                         {"match": {
                                             "date": date}},
                                         {"match": {
                                             "texte": "\"@when\":\"" + date}},
                                         {"match": {
                                             "texte": "\"titleStmt\": {\"title\":" + text}},
                                         {"match": {
                                             "texte": "\"monogr\": {\"title\": {" + text}},
                                         {"match": {
                                             "texte": "\"sourceDesc\": { \"biblStruct\": { \"analytic\": {\"author\": {\"persName\": {" + text}},
                                         {"match": {
                                             "texte": "\"@type\": \"references\", \"listBibl\": {\"biblStruct\": [ { \"author\": [" + text}},
                                         {"match": {
                                             "texte": "\"orgName\": {" + text}},
                                         {"match": {
                                             "texte": "\"keywords\": {" + text}}], }}})

            meta = Metadata_STAB_ISSW.query.filter(
                Metadata_STAB_ISSW.ID.in_([hit["_id"] for hit in complexsearch['hits']['hits']])
            ).all()

            metadata_auteurs_et_titres = {}

            for chaque_resultat in meta:
                metadata_auteurs_et_titres[chaque_resultat.ID] = {
                    "titre": chaque_resultat.Titre,
                    "auteur": chaque_resultat.Auteurs,
                }

            # Création de la variable contenant les noms de colonnes pour le fichiers de résultat.
            csv_columns = ['ID', 'Titre', 'Auteurs']

            try:
                # On ouvre un fichier au format csv dans le dossier Results,
                with open('/home/max5452/Bureau/ShipStabResearchApp/Elasticsearch_APP/app/static/Results/' + text + '_' + date + '.csv', 'w') as csvfile:
                    # On écrit les noms de colonnes et on définit la virgule comme délimiteur.
                    writer = csv.DictWriter(csvfile, fieldnames=csv_columns, delimiter=',')
                    writer.writeheader()
                    # pour chaque résultat récupérer dans meta, on écrit un dictionnaire contenant ID, Titre et Auteur.
                    for chaque_resultat in meta:
                        writer.writerow({'ID': chaque_resultat.ID,
                                         'Titre': chaque_resultat.Titre,
                                         'Auteurs': chaque_resultat.Auteurs})
            # En cas d'erreur lors de l'ouverture/la création du fichier, on affiche une erreur I/O.
            except IOError:
                print("I/O error.")

            return render_template('complex_result.html', q=text, date=date, response=complexsearch,
                                   metadata=metadata_auteurs_et_titres, count=count)
        # Si rien n'est sélectionné, alors on procède à une recherche simple (texte + date).
        else:
            complex_search = es.search(index='stability',
                                       doc_type='article',
                                       body={"size": 1000, "query": {
                                           "bool": {
                                               "must": {"match_phrase": {"texte": "\"body\": {" + text}},
                                               "should": {"match": {"date": date}}}}
                                             }
                                       )

            count = es.count(index='stability',
                             doc_type='article',
                             body={"query": {
                                 "bool": {
                                     "must": {"match_phrase": {"texte": "\"body\": {" + text}},
                                     "should": {"match": {"date": date}}}}
                             })

            meta = Metadata_STAB_ISSW.query.filter(
                Metadata_STAB_ISSW.ID.in_([hit["_id"] for hit in complex_search['hits']['hits']])
            ).all()

            metadata_auteurs_et_titres = {}

            for chaque_resultat in meta:
                metadata_auteurs_et_titres[chaque_resultat.ID] = {
                    "titre": chaque_resultat.Titre,
                    "auteur": chaque_resultat.Auteurs,
                }

        # Création de la variable contenant les noms de colonnes pour le fichiers de résultat.
        csv_columns = ['ID', 'Titre', 'Auteurs']

        try:
            # On ouvre un fichier au format csv dans le dossier Results,
            with open('/home/max545/Bureau/ShipStabResearchApp/Elasticsearch_APP/app/static/Results/' + text + '.csv', 'w') as csvfile:
                # On écrit les noms de colonnes et on définit la virgule comme délimiteur.
                writer = csv.DictWriter(csvfile, fieldnames=csv_columns, delimiter=',')
                writer.writeheader()
                # pour chaque résultat récupérer dans meta, on écrit un dictionnaire contenant ID, Titre et Auteur.
                for chaque_resultat in meta:
                    writer.writerow({'ID': chaque_resultat.ID,
                                     'Titre': chaque_resultat.Titre,
                                     'Auteurs': chaque_resultat.Auteurs})
                # En cas d'erreur lors de l'ouverture/la création du fichier, on affiche une erreur I/O.
        except IOError:
            print("I/O error.")

            return render_template('complex_result.html', q=text, date=date, response=complex_search,
                                   metadata=metadata_auteurs_et_titres, count=count)
    return render_template('complex_research.html')


@app.route('/keywords_analysis', methods=["GET", "POST"])
def keywords_analysis():
    keyword = "intact stability"
    result = es.search(
        index='stability',
        doc_type='article',
        body={"size": 100, "query": {
            "bool": {
                "must": {"match_phrase_prefix": {"texte": {"query": "\"keywords\": {" + keyword, "slop": 20}}}
            }}}
    )

    meta = Metadata_STAB_ISSW.query.filter(
        Metadata_STAB_ISSW.ID.in_([hit["_id"] for hit in result['hits']['hits']])
    ).all()

    metadata_auteurs_et_titres = {}

    for chaque_resultat in meta:
        metadata_auteurs_et_titres[chaque_resultat.ID] = {
            "titre": chaque_resultat.Titre,
            "auteur": chaque_resultat.Auteurs,
            "keyword": chaque_resultat.keywords
        }

    return render_template('keywords_analysis.html', response=result, metadata=metadata_auteurs_et_titres)
