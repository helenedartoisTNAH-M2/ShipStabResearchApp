from elasticsearch import Elasticsearch

es = Elasticsearch()

with open('/home/grobid/Bureau/texte.txt', mode='w') as fichier:
    ref_r = es.search(index='stability', doc_type='article', body={"size": 2000,
                                                                   "query": {
                                                                       "match": {
                                                                           "texte": "\"back\": {\"div\": [{\"@type\": \"references\",\"listBibl\": {\"biblStruct\": [{"
                                                                       }}})
    biblio = str(ref_r)
    fichier.write(biblio)


