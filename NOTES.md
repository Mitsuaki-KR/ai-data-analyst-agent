# Notes de développement — bugs et décisions

Ce fichier documente chaque bug réel rencontré, sa cause exacte et sa solution.


## Bug #1 — `_create_indexes` suppose un schéma complet (06/09/2026)

**Symptôme** : `sqlite3.OperationalError: no such table: main.order_payments`
lors de `pytest tests/test_ingestion.py`, sur 3 tests sur 5.

**Cause exacte** : `_create_indexes` contenait une liste d'instructions
`CREATE INDEX` codée en dur pour les 8 tables de production, sans vérifier
qu'elles existaient. Le fixture de test ne charge que 2 tables
(`orders`, `order_items`) pour rester rapide — dès que la fonction tentait
d'indexer `order_payments`, absente de cette base de test, ça crashait.

**Pourquoi ce n'était pas visible avant** : en exécution normale
(`python -m src.ingestion.load_to_sqlite`), les 8 tables sont toujours
chargées, donc le bug était invisible en usage réel — seul un test avec
un sous-ensemble de tables pouvait le révéler. Bon exemple de pourquoi
tester avec des données minimales/synthétiques (et pas seulement le
dataset complet) attrape des bugs de couplage caché.

**Correction** : `_create_indexes` interroge désormais `sqlite_master`
pour ne créer un index que si la table cible existe réellement.




## Bug #2 — Test mal isolé, pas un bug de sécurité (07/09/2026)

**Symptôme** : `test_forbidden_keyword_inside_select_is_rejected` échoue avec
`AssertionError: Regex pattern did not match` — attendait "interdits", a reçu
"Plusieurs instructions".

**Cause exacte** : le test utilisait un input combinant deux vecteurs d'attaque
en même temps (point-virgule ET mot-clé DROP). Le validateur bloque bien la
requête, mais sur la première vérification qu'il rencontre (anti-injection
multi-requêtes), jamais atteint la vérification des mots-clés. Le validateur
fonctionne correctement — c'est le test qui ne testait pas isolément le
comportement visé.

**Leçon** : un test doit isoler une seule condition à la fois. Un input
combinant plusieurs vecteurs d'attaque valide bien la sécurité globale,
mais ne garantit pas que chaque règle individuelle fonctionne — un futur
refactor pourrait supprimer la vérification multi-requêtes sans que ce
test ne s'en aperçoive.

**Correction** : nouvel input à instruction unique (`WITH x AS (DELETE FROM
orders) SELECT * FROM x`) qui isole spécifiquement le scan de mots-clés.


## Bug #3 — Progress handler trop grossier ne détecte pas les requêtes courtes (07/09/2026)

**Symptôme** : `test_slow_query_is_interrupted_by_timeout` échoue avec
"DID NOT RAISE SQLExecutionError" — la requête censée être lente s'exécute
sans être interrompue.

**Cause exacte** : `set_progress_handler(handler, n=1000)` n'appelle le
callback qu'après 1000 instructions VM SQLite. Le produit cartésien de test
(3^6 = 729 lignes) se terminait avant d'atteindre ce seuil — le callback
n'était jamais invoqué, donc le timeout jamais vérifié.

**Pourquoi c'est plus qu'un problème de test** : ça révèle qu'avec n=1000,
même en production, une requête un peu lourde mais rapide pourrait échapper
à la vérification de timeout si elle finit avant le premier callback.

**Correction** : n abaissé à 100 (vérification plus fréquente, coût
négligeable), et jeu de données de test agrandi (50 lignes x 5 tables en
produit cartésien) pour garantir une requête réellement longue, plutôt
qu'un timeout microscopique impossible à mesurer de façon fiable.