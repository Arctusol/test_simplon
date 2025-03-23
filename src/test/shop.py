import sqlite3
import pandas as pd
import requests
import os

# Connexion à SQLite
db_path = os.getenv("DATABASE_PATH", "/db/magasins.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Création de la table ventes si elle n’existe pas
cursor.execute("""
CREATE TABLE IF NOT EXISTS magasins (
    id INTEGER PRIMARY KEY,
    Magasin TEXT,
    Ville TEXT,
    Nombre de salariés TEXT
)
""")
conn.commit()

# Téléchargement des données
csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSawI56WBC64foMT9pKCiY594fBZk9Lyj8_bxfgmq-8ck_jw1Z49qDeMatCWqBxehEVoM6U1zdYx73V/pub?gid=714623615&single=true&output=csv"
data = requests.get(csv_url).content
df = pd.read_csv(pd.compat.StringIO(data.decode('utf-8')))

# Insertion des nouvelles données
for _, row in df.iterrows():
    cursor.execute("INSERT INTO magasins (Magasin, Ville, Nombre de salariés) VALUES (?, ?, ?)", 
                   (row["Magasin"], row["Ville"], row["Nombre de salariés"]))

conn.commit()

# Analyse : chiffre d’affaires total
cursor.execute("SELECT SUM(Nombre de salariés) FROM magasins")
total_employe = cursor.fetchone()[0]
print(f"Nombre de salariés en France : {total_employe} €")

conn.close()