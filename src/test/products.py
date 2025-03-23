import sqlite3
import pandas as pd
import requests
import os

# Connexion à SQLite
db_path = os.getenv("DATABASE_PATH", "/db/products.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Création de la table products si elle n’existe pas
cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    Nom TEXT
    ID Référence produit PRIMARY KEY,
    Prix REAL,
    Stock REAL,
)
""")
conn.commit()

# Téléchargement des données
csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSawI56WBC64foMT9pKCiY594fBZk9Lyj8_bxfgmq-8ck_jw1Z49qDeMatCWqBxehEVoM6U1zdYx73V/pub?gid=0&single=true&output=csv"
data = requests.get(csv_url).content
df = pd.read_csv(pd.compat.StringIO(data.decode('utf-8')))

# Insertion des nouvelles données
for _, row in df.iterrows():
    cursor.execute("INSERT INTO products (Nom, ID Référence produit, Prix, Stock) VALUES (?, ?, ?, ?)", 
                   (row["Nom"], row["ID Référence produit"], row["Prix"], row["Stock"]))

conn.commit()

# Analyse : chiffre d’affaires total
cursor.execute("SELECT SUM(Stock) FROM products")
total_stock = cursor.fetchone()[0]
print(f"Chiffre d'affaires total : {total_stock} €")

conn.close()