"""
Tests du module d'ingestion.

Design : on ne teste jamais avec le vrai dataset Olist (trop lourd, trop lent,
et un test ne doit pas dépendre d'un fichier externe volumineux). On crée
des mini-CSV synthétiques dans un dossier temporaire (fixture pytest `tmp_path`)
qui reproduisent la même structure de clés/colonnes.
"""
import sqlite3

import pandas as pd
import pytest

from src.ingestion.load_to_sqlite import load_csvs_to_sqlite, IngestionError
from src.ingestion import config


@pytest.fixture
def fake_raw_dir(tmp_path, monkeypatch):
    """
    Crée un faux dossier data/raw avec des CSV minimalistes pour 2 tables,
    et redirige CSV_TO_TABLE pour ne tester que ces 2 tables (pas les 8),
    afin que le test reste rapide et focalisé.
    """
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    orders_df = pd.DataFrame({
        "order_id": ["o1", "o2", "o3"],
        "customer_id": ["c1", "c2", "c1"],
    })
    orders_df.to_csv(raw_dir / "olist_orders_dataset.csv", index=False)

    items_df = pd.DataFrame({
        "order_id": ["o1", "o2", "o3"],
        "product_id": ["p1", "p2", "p1"],
        "price": [10.5, 20.0, 15.0],
    })
    items_df.to_csv(raw_dir / "olist_order_items_dataset.csv", index=False)

    # On restreint temporairement le mapping aux 2 fichiers créés ci-dessus,
    # pour ne pas exiger les 8 fichiers du vrai dataset dans ce test unitaire.
    monkeypatch.setattr(config, "CSV_TO_TABLE", {
        "olist_orders_dataset.csv": "orders",
        "olist_order_items_dataset.csv": "order_items",
    })
    # load_to_sqlite importe CSV_TO_TABLE directement depuis config au moment
    # du module load — on patche donc aussi la référence utilisée dans le module cible.
    import src.ingestion.load_to_sqlite as load_module
    monkeypatch.setattr(load_module, "CSV_TO_TABLE", config.CSV_TO_TABLE)

    return raw_dir


def test_load_creates_correct_row_counts(fake_raw_dir, tmp_path):
    """
    Vérifie que le nombre de lignes chargées correspond exactement
    au nombre de lignes des CSV sources — détecte une perte ou
    duplication silencieuse de données pendant le chargement.
    """
    db_path = tmp_path / "test.sqlite"
    counts = load_csvs_to_sqlite(fake_raw_dir, db_path)

    assert counts == {"orders": 3, "order_items": 3}


def test_load_creates_queryable_tables(fake_raw_dir, tmp_path):
    """
    Vérifie que les tables créées sont réellement interrogeables en SQL
    avec les bonnes colonnes — pas juste que pandas n'a pas planté.
    """
    db_path = tmp_path / "test.sqlite"
    load_csvs_to_sqlite(fake_raw_dir, db_path)

    conn = sqlite3.connect(db_path)
    result = conn.execute("SELECT customer_id FROM orders WHERE order_id = 'o1'").fetchone()
    conn.close()

    assert result == ("c1",)


def test_load_is_idempotent(fake_raw_dir, tmp_path):
    """
    Vérifie qu'exécuter l'ingestion deux fois de suite ne duplique pas
    les données (grâce à if_exists='replace'). Ce test protège contre
    une régression future si quelqu'un change 'replace' en 'append'
    sans réaliser les conséquences.
    """
    db_path = tmp_path / "test.sqlite"
    load_csvs_to_sqlite(fake_raw_dir, db_path)
    load_csvs_to_sqlite(fake_raw_dir, db_path)  # deuxième exécution

    conn = sqlite3.connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    conn.close()

    assert count == 3  # pas 6


def test_missing_csv_raises_clear_error(tmp_path):
    """
    Vérifie qu'un dossier data/raw incomplet (fichier manquant) déclenche
    une erreur explicite et compréhensible, plutôt qu'un stack trace
    pandas cryptique ("FileNotFoundError" générique). C'est le genre
    d'erreur que TU vas rencontrer en pratique si le téléchargement
    Kaggle a raté un fichier — le message doit t'aider à comprendre quoi faire.
    """
    empty_raw_dir = tmp_path / "empty_raw"
    empty_raw_dir.mkdir()
    db_path = tmp_path / "test.sqlite"

    with pytest.raises(IngestionError, match="introuvable"):
        load_csvs_to_sqlite(empty_raw_dir, db_path)


def test_missing_raw_dir_raises_clear_error(tmp_path):
    """
    Vérifie le cas où le dossier data/raw lui-même n'existe pas
    (typiquement : première exécution avant tout téléchargement).
    """
    nonexistent_dir = tmp_path / "does_not_exist"
    db_path = tmp_path / "test.sqlite"

    with pytest.raises(IngestionError, match="introuvable"):
        load_csvs_to_sqlite(nonexistent_dir, db_path)