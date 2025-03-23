import sqlite3
import pandas as pd
import requests
import os
from io import StringIO
from datetime import datetime

def setup_database():
    os.makedirs("/db", exist_ok=True)
    conn = sqlite3.connect('/db/analysis.db')
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ventes (
        date DATE,
        ID_Reference_produit TEXT,
        Quantite INTEGER,
        ID_Magasin INTEGER,
        PRIMARY KEY (date, ID_Reference_produit, ID_Magasin)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS produits (
        Nom TEXT,
        ID_Reference_produit TEXT PRIMARY KEY,
        Prix REAL,
        Stock INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS magasins (
        ID_Magasin INTEGER PRIMARY KEY,
        Ville TEXT,
        Nombre_de_salaries INTEGER
    )
    """)
    
    conn.commit()
    return conn, cursor

def load_csv_from_url(url):
    df = pd.read_csv(url)
    # Rename problematic columns
    print(f"Colonnes disponibles : {df.columns.tolist()}")
    return df

def analyze_data():
    try:
        print("Initialisation de la base de données...")
        conn, cursor = setup_database()

        urls = {
            "ventes": "https://docs.google.com/spreadsheets/d/e/2PACX-1vSawI56WBC64foMT9pKCiY594fBZk9Lyj8_bxfgmq-8ck_jw1Z49qDeMatCWqBxehEVoM6U1zdYx73V/pub?gid=760830694&single=true&output=csv",
            "produits": "https://docs.google.com/spreadsheets/d/e/2PACX-1vSawI56WBC64foMT9pKCiY594fBZk9Lyj8_bxfgmq-8ck_jw1Z49qDeMatCWqBxehEVoM6U1zdYx73V/pub?gid=0&single=true&output=csv",
            "magasins": "https://docs.google.com/spreadsheets/d/e/2PACX-1vSawI56WBC64foMT9pKCiY594fBZk9Lyj8_bxfgmq-8ck_jw1Z49qDeMatCWqBxehEVoM6U1zdYx73V/pub?gid=714623615&single=true&output=csv"
        }

        # Import des données de référence (produits et magasins)
        # Utilisation de INSERT OR IGNORE pour éviter les doublons sur les clés primaires
        print("Import des données de produits...")
        df_produits = load_csv_from_url(urls["produits"])
        for _, row in df_produits.iterrows():
            cursor.execute(
                "INSERT OR IGNORE INTO produits (Nom, ID_Reference_produit, Prix, Stock) VALUES (?, ?, ?, ?)",
                (row["Nom"], row["ID Référence produit"], row["Prix"], row["Stock"])
            )

        print("Import des données de magasins...")
        df_magasins = load_csv_from_url(urls["magasins"])
        for _, row in df_magasins.iterrows():
            cursor.execute(
                "INSERT OR IGNORE INTO magasins (ID_Magasin, Ville, Nombre_de_salaries) VALUES (?, ?, ?)",
                (row["ID Magasin"], row["Ville"], row["Nombre de salariés"])
            )

        print("Import des données de ventes...")
        df_ventes = load_csv_from_url(urls["ventes"])
        date_column = 'Date' if 'Date' in df_ventes.columns else 'date'
        
        # Convertir la colonne date avant la boucle
        dates = pd.to_datetime(df_ventes[date_column]).dt.strftime('%Y-%m-%d')
        
        for idx, row in df_ventes.iterrows():
            cursor.execute(
                "INSERT OR IGNORE INTO ventes (date, ID_Reference_produit, Quantite, ID_Magasin) VALUES (?, ?, ?, ?)",
                (dates.iloc[idx], row["ID Référence produit"], row["Quantité"], row["ID Magasin"])
            )

        conn.commit()

        print("\nAnalyse des données...")
        
        # Calcul du chiffre d'affaires total
        cursor.execute("""
            SELECT SUM(v.Quantite * p.Prix)
            FROM ventes v
            JOIN produits p ON v.ID_Reference_produit = p.ID_Reference_produit
        """)
        chiffre_affaires = cursor.fetchone()[0]

        # Calcul du chiffre d'affaires par magasin
        cursor.execute("""
            SELECT m.ID_Magasin, m.Ville, SUM(v.Quantite * p.Prix) as chiffre_affaires
            FROM ventes v
            JOIN produits p ON v.ID_Reference_produit = p.ID_Reference_produit
            JOIN magasins m ON v.ID_Magasin = m.ID_Magasin
            GROUP BY m.ID_Magasin, m.Ville
            ORDER BY chiffre_affaires DESC
        """)
        ca_par_magasin = cursor.fetchall()
        
        # Calcul de la valeur du stock en attente
        cursor.execute("""
            SELECT SUM(Prix * Stock) as valeur_stock
            FROM produits
        """)
        valeur_stock = cursor.fetchone()[0]
        
        # Calcul des ventes par produit
        cursor.execute("""
            SELECT
                p.Nom,
                SUM(v.Quantite) as quantite_totale,
                SUM(v.Quantite * p.Prix) as chiffre_affaires
            FROM ventes v
            JOIN produits p ON v.ID_Reference_produit = p.ID_Reference_produit
            GROUP BY p.ID_Reference_produit, p.Nom
            ORDER BY chiffre_affaires DESC
        """)
        ventes_par_produit = cursor.fetchall()
        
        cursor.execute("SELECT SUM(Stock) FROM produits")
        total_stock = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(Nombre_de_salaries) FROM magasins")
        total_employes = cursor.fetchone()[0]

        print("\nRésultats :")
        print(f"Chiffre d'affaires total : {chiffre_affaires:.2f} €")
        
        print(f"\nChiffre d'affaires par magasin :")
        for magasin in ca_par_magasin:
            print(f"- {magasin[1]} (ID: {magasin[0]}): {magasin[2]:.2f} €")
            
        print(f"\nVentes par produit :")
        for produit in ventes_par_produit:
            print(f"- {produit[0]}: {produit[1]} unités, CA: {produit[2]:.2f} €")
            
        print(f"\nStock :")
        print(f"- Quantité totale en stock : {total_stock}")
        print(f"- Valeur totale du stock : {valeur_stock:.2f} €")
        
        print(f"\nNombre total d'employés : {total_employes}")

    except Exception as e:
        print(f"Erreur : {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    analyze_data()
