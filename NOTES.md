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