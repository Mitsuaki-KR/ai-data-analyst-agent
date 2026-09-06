"""
Configuration centralisée du module d'ingestion.

Pourquoi un fichier config séparé : les chemins et le mapping des tables
sont utilisés à la fois par le script de chargement ET par les tests.
Les centraliser ici évite de dupliquer ces valeurs (et le risque
qu'elles divergent) entre le code de prod et les tests.
"""
from pathlib import Path

# Chemins relatifs à la racine du projet, jamais en dur ("C:\Users\...")
# pour que le projet fonctionne sur n'importe quelle machine (portabilité).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
DB_PATH = PROJECT_ROOT / "data" / "db" / "olist.sqlite"

# Mapping nom_de_fichier_csv -> nom_de_table_sql
# Pourquoi un dict explicite plutôt que de déduire le nom de table du nom
# de fichier automatiquement : les noms de fichiers Olist sont verbeux
# ("olist_order_items_dataset.csv"), on veut des noms de table courts
# et lisibles dans les requêtes SQL générées par l'agent plus tard.
CSV_TO_TABLE = {
    "olist_orders_dataset.csv": "orders",
    "olist_order_items_dataset.csv": "order_items",
    "olist_products_dataset.csv": "products",
    "olist_customers_dataset.csv": "customers",
    "olist_sellers_dataset.csv": "sellers",
    "olist_order_payments_dataset.csv": "order_payments",
    "olist_order_reviews_dataset.csv": "order_reviews",
    "product_category_name_translation.csv": "product_category_translation",
}