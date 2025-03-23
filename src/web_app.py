import gradio as gr
import pygwalker as pyg
import pandas as pd
import sqlite3
from pygwalker.api.gradio import PYGWALKER_ROUTE, get_html_on_gradio

def load_data():
    """Charge l'ensemble des données depuis SQLite en DataFrames pandas"""
    conn = sqlite3.connect('/db/analysis.db')
    
    # Chargement des ventes détaillées
    df_ventes = pd.read_sql_query("""
        SELECT
            v.date,
            v.Quantite,
            p.Nom as Produit,
            p.Prix,
            m.Ville,
            m.Nombre_de_salaries as Effectif,
            (v.Quantite * p.Prix) as Chiffre_Affaires
        FROM ventes v
        JOIN produits p ON v.ID_Reference_produit = p.ID_Reference_produit
        JOIN magasins m ON v.ID_Magasin = m.ID_Magasin
        ORDER BY v.date
    """, conn)
    
    # Chargement des données RH et magasins
    df_magasins = pd.read_sql_query("""
        SELECT
            ID_Magasin,
            Ville,
            Nombre_de_salaries as Effectif,
            (SELECT SUM(v.Quantite * p.Prix)
             FROM ventes v
             JOIN produits p ON v.ID_Reference_produit = p.ID_Reference_produit
             WHERE v.ID_Magasin = m.ID_Magasin) as CA_Total
        FROM magasins m
        ORDER BY Ville
    """, conn)
    
    # Chargement des données produits avec statistiques
    df_produits = pd.read_sql_query("""
        SELECT
            p.ID_Reference_produit,
            p.Nom as Produit,
            p.Prix,
            p.Stock,
            SUM(v.Quantite) as Total_Ventes,
            SUM(v.Quantite * p.Prix) as CA_Total
        FROM produits p
        LEFT JOIN ventes v ON p.ID_Reference_produit = v.ID_Reference_produit
        GROUP BY p.ID_Reference_produit, p.Nom, p.Prix, p.Stock
        ORDER BY CA_Total DESC
    """, conn)
    
    # Conversion de la colonne date
    df_ventes['date'] = pd.to_datetime(df_ventes['date'])
    
    conn.close()
    return df_ventes, df_magasins, df_produits

# Configuration de l'interface Gradio
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Dashboard d'Analyse des Ventes")
    gr.Markdown("""
    ##Explorez vos données :
    - 📊 Ventes : Analyse complète des ventes et performances
    - 👥 RH & Magasins : Informations sur les effectifs et performances par magasin
    - 📦 Produits : Catalogue et statistiques produits
    """)
    
    try:
        # Chargement de toutes les données
        df_ventes, df_magasins, df_produits = load_data()
        
        with gr.Tabs():
            # Tab Ventes
            with gr.Tab("📊 Analyse des ventes"):
                gr.Markdown("### Analyse détaillée des ventes")
                pyg_ventes = get_html_on_gradio(
                    df_ventes,
                    spec="./viz-config-ventes.json",
                    use_kernel_calc=True
                )
                gr.HTML(pyg_ventes)
                
                # Deuxième visualisation des ventes
                gr.Markdown("### Analyse complémentaire des ventes")
                pyg_ventes2 = get_html_on_gradio(
                    df_ventes,
                    spec="./viz-config-ventes2.json",
                    use_kernel_calc=True
                )
                gr.HTML(pyg_ventes2)
            
            # Tab RH & Magasins
            with gr.Tab("👥 RH & Magasins"):
                gr.Markdown("### Données RH et performances des magasins")
                pyg_magasins = get_html_on_gradio(
                    df_magasins,
                    spec="./viz-config-magasins.json",
                    use_kernel_calc=True
                )
                gr.HTML(pyg_magasins)
            
            # Tab Produits
            with gr.Tab("📦 Catalogue produits"):
                gr.Markdown("### Analyse du catalogue et des ventes par produit")
                pyg_produits = get_html_on_gradio(
                    df_produits,
                    spec="./viz-config-produits.json",
                    use_kernel_calc=True
                )
                gr.HTML(pyg_produits)
        
    except Exception as e:
        gr.Error(f"Erreur lors du chargement des données: {str(e)}")

# Configuration du serveur pour Docker
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        app_kwargs={"routes": [PYGWALKER_ROUTE]}
    )