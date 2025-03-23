import sqlite3
import pandas as pd
import requests
import os

# Connexion à SQLite
db_path = os.getenv("DATABASE_PATH", "/db/sales.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Création de la table ventes si elle n’existe pas
cursor.execute("""
CREATE TABLE IF NOT EXISTS ventes (
    id INTEGER PRIMARY KEY,
    produit TEXT,
    montant REAL,
    region TEXT,
    date TEXT
)
""")
conn.commit()

# Téléchargement des données
csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSawI56WBC64foMT9pKCiY594fBZk9Lyj8_bxfgmq-8ck_jw1Z49qDeMatCWqBxehEVoM6U1zdYx73V/pub?gid=0&single=true&output=csv"
data = requests.get(csv_url).content
df = pd.read_csv(pd.compat.StringIO(data.decode('utf-8')))

# Insertion des nouvelles données
for _, row in df.iterrows():
    cursor.execute("INSERT INTO ventes (produit, montant, region, date) VALUES (?, ?, ?, ?)", 
                   (row["produit"], row["montant"], row["region"], row["date"]))

conn.commit()

# Analyse : chiffre d’affaires total
cursor.execute("SELECT SUM(montant) FROM ventes")
chiffre_affaires = cursor.fetchone()[0]
print(f"Chiffre d'affaires total : {chiffre_affaires} €")

conn.close()