import sqlite3
import pandas as pd
import requests
import os
import time
import schedule
import pytz
import logging
from datetime import datetime

# Create logs directory
os.makedirs('/app/logs', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/data_fetcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
    logger.info(f"Colonnes disponibles : {df.columns.tolist()}")
    return df

from csv_exporter import CSVExporter

def analyze_data():
    try:
        logger.info("Initialisation de la base de données...")
        conn, cursor = setup_database()
        
        # Initialize CSV exporter
        csv_exporter = CSVExporter()

        # Dictionary of CSV URLs
        urls = {
            "ventes": "https://docs.google.com/spreadsheets/d/e/2PACX-1vSawI56WBC64foMT9pKCiY594fBZk9Lyj8_bxfgmq-8ck_jw1Z49qDeMatCWqBxehEVoM6U1zdYx73V/pub?gid=760830694&single=true&output=csv",
            "produits": "https://docs.google.com/spreadsheets/d/e/2PACX-1vSawI56WBC64foMT9pKCiY594fBZk9Lyj8_bxfgmq-8ck_jw1Z49qDeMatCWqBxehEVoM6U1zdYx73V/pub?gid=0&single=true&output=csv",
            "magasins": "https://docs.google.com/spreadsheets/d/e/2PACX-1vSawI56WBC64foMT9pKCiY594fBZk9Lyj8_bxfgmq-8ck_jw1Z49qDeMatCWqBxehEVoM6U1zdYx73V/pub?gid=714623615&single=true&output=csv"
        }

        # Import des données de référence (produits et magasins)
        # Utilisation de INSERT OR IGNORE pour éviter les doublons sur les clés primaires
        logger.info("Import des données de produits...")
        df_produits = load_csv_from_url(urls["produits"])
        for _, row in df_produits.iterrows():
            cursor.execute(
                "INSERT OR IGNORE INTO produits (Nom, ID_Reference_produit, Prix, Stock) VALUES (?, ?, ?, ?)",
                (row["Nom"], row["ID Référence produit"], row["Prix"], row["Stock"])
            )

        logger.info("Import des données de magasins...")
        df_magasins = load_csv_from_url(urls["magasins"])
        for _, row in df_magasins.iterrows():
            cursor.execute(
                "INSERT OR IGNORE INTO magasins (ID_Magasin, Ville, Nombre_de_salaries) VALUES (?, ?, ?)",
                (row["ID Magasin"], row["Ville"], row["Nombre de salariés"])
            )

        logger.info("Import des données de ventes...")
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

        logger.info("\nAnalyse des données...")
        
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

        # Display results
        logger.info("\nRésultats:")
        logger.info(f"Chiffre d'affaires total : {chiffre_affaires:.2f} €")

        logger.info("\nChiffre d'affaires par magasin:")
        for magasin in ca_par_magasin:
            logger.info(f"- {magasin[1]} (ID: {magasin[0]}): {magasin[2]:.2f} €")

        logger.info("\nVentes par produit:")
        for produit in ventes_par_produit:
            logger.info(f"- {produit[0]}: {produit[1]} unités, CA: {produit[2]:.2f} €")
        
        logger.info("\nStock:")
        logger.info(f"- Quantité totale en stock : {total_stock}")
        logger.info(f"- Valeur totale du stock : {valeur_stock:.2f} €")

        logger.info(f"\nNombre total d'employés : {total_employes}")

        # Export all data to CSV files
        analysis_results = {
            'total_revenue': chiffre_affaires,
            'total_employees': total_employes,
            'store_data': [(m[0], m[1], m[2], cursor.execute("SELECT Nombre_de_salaries FROM magasins WHERE ID_Magasin = ?", (m[0],)).fetchone()[0])
                          for m in ca_par_magasin],
            'product_data': ventes_par_produit,
            'total_stock': total_stock,
            'stock_value': valeur_stock
        }
        
        csv_exporter.export_all_data(analysis_results)
        logger.info("CSV export completed successfully")

    except Exception as e:
        logger.error(f"Erreur : {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

def fetch_and_process_data():
    """Wrapper function for analyze_data() with logging"""
    logger.info("Starting scheduled data fetch")
    try:
        analyze_data()
        logger.info("Data fetch and analysis completed successfully")
    except Exception as e:
        logger.error(f"Error during data fetch: {str(e)}")

def run_scheduler():
    """Main scheduler function"""
    # Use Paris timezone
    paris_tz = pytz.timezone('Europe/Paris')
    current_time = datetime.now(paris_tz)
    
    logger.info(f"Starting scheduler at {current_time}")
    
    # Schedule jobs at noon and midnight Paris time
    schedule.every().day.at("00:00").do(fetch_and_process_data)
    schedule.every().day.at("12:00").do(fetch_and_process_data)
    
    # Run initial data fetch
    logger.info("Running initial data fetch...")
    fetch_and_process_data()
    
    # Run the scheduler
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Scheduler error: {str(e)}")
            # Wait before retrying
            time.sleep(300)  # 5 minutes

if __name__ == "__main__":
    run_scheduler()
