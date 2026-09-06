"""
Charge les CSV Olist dans une base SQLite locale.

Design : ce module expose une fonction pure `load_csvs_to_sqlite(raw_dir, db_path)`
qui prend des chemins en paramètres, plutôt que de lire directement config.py
en dur à l'intérieur. Pourquoi : ça rend la fonction testable avec des
dossiers temporaires (voir tests/test_ingestion.py) sans toucher aux
vraies données du projet.
"""
import sqlite3
import logging
from pathlib import Path

import pandas as pd

from src.ingestion.config import CSV_TO_TABLE

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class IngestionError(Exception):
    """Erreur explicite pour tout problème d'ingestion.

    Pourquoi une exception custom plutôt que de laisser remonter les
    exceptions pandas/sqlite brutes : ça permet à l'appelant (et aux tests)
    de distinguer "une erreur d'ingestion attendue" d'un bug inattendu
    ailleurs dans le code.
    """
    pass


def load_csvs_to_sqlite(raw_dir: Path, db_path: Path) -> dict[str, int]:
    """
    Charge chaque CSV listé dans CSV_TO_TABLE vers une table SQLite.

    Retourne un dict {nom_table: nombre_de_lignes_chargées}, utile pour
    la validation et pour les tests (on vérifie le contenu du retour,
    pas seulement l'absence d'exception).
    """
    if not raw_dir.exists():
        raise IngestionError(f"Dossier de données brutes introuvable : {raw_dir}")

    # On crée le dossier parent de la DB s'il n'existe pas encore
    # (évite un crash sqlite3 "unable to open database file" au premier lancement).
    db_path.parent.mkdir(parents=True, exist_ok=True)

    row_counts: dict[str, int] = {}

    # Pourquoi une connexion unique réutilisée pour toutes les tables plutôt
    # qu'une connexion par table : on veut que l'ingestion soit atomique-ish
    # dans une seule transaction logique, et éviter le coût d'ouverture
    # répétée de la même DB.
    conn = sqlite3.connect(db_path)
    try:
        for csv_filename, table_name in CSV_TO_TABLE.items():
            csv_path = raw_dir / csv_filename

            if not csv_path.exists():
                raise IngestionError(
                    f"Fichier CSV attendu introuvable : {csv_path}. "
                    f"As-tu bien téléchargé et extrait le dataset Olist dans {raw_dir} ?"
                )

            logger.info(f"Chargement de {csv_filename} -> table '{table_name}'")

            df = pd.read_csv(csv_path)

            # if_exists="replace" : chaque exécution du script repart d'un
            # état propre plutôt que d'accumuler des doublons si on relance
            # l'ingestion plusieurs fois (idempotence — testée explicitement).
            df.to_sql(table_name, conn, if_exists="replace", index=False)

            row_counts[table_name] = len(df)
            logger.info(f"  -> {len(df)} lignes chargées dans '{table_name}'")

        _create_indexes(conn)
        conn.commit()
    finally:
        conn.close()

    return row_counts


def _create_indexes(conn: sqlite3.Connection) -> None:
    """
    Ajoute des index sur les colonnes de jointure fréquentes, uniquement
    pour les tables qui existent réellement dans cette base.

    Pourquoi cette vérification d'existence (bug rencontré le 06/09) :
    en environnement de test, on charge volontairement un sous-ensemble
    des tables (ex: seulement 'orders' et 'order_items') pour garder les
    tests rapides et ciblés. La première version de cette fonction
    listait les index en dur pour les 8 tables de production, en supposant
    implicitement qu'elles existaient toutes. Résultat : crash
    "no such table: main.order_payments" dès qu'on chargeait un
    sous-ensemble de tables. La fonction doit être robuste à un schéma
    partiel, pas seulement au schéma complet de prod.
    """
    index_statements = [
        ("order_items", "CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id)"),
        ("order_items", "CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id)"),
        ("orders", "CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id)"),
        ("order_payments", "CREATE INDEX IF NOT EXISTS idx_order_payments_order_id ON order_payments(order_id)"),
        ("order_reviews", "CREATE INDEX IF NOT EXISTS idx_order_reviews_order_id ON order_reviews(order_id)"),
    ]

    existing_tables = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }

    for table_name, stmt in index_statements:
        if table_name in existing_tables:
            conn.execute(stmt)
        else:
            logger.debug(f"Table '{table_name}' absente de cette base — index ignoré ({stmt})")


if __name__ == "__main__":
    from src.ingestion.config import RAW_DATA_DIR, DB_PATH

    counts = load_csvs_to_sqlite(RAW_DATA_DIR, DB_PATH)
    logger.info(f"Ingestion terminée. Résumé : {counts}")