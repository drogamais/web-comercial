# database/common_db.py
import mysql.connector
from mysql.connector import Error
from flask import g
from config import DB_CONFIG # Precisa importar a configuração

# --- NOVAS FUNÇÕES PARA VALIDAR GTIN NO dbDrogamais ---

def get_drogamais_db_connection():
    """
    Cria uma nova conexão de banco de dados especificamente para o dbDrogamais.
    (VERSÃO CORRIGIDA - Não herda 'collation')
    """
    try:
        config_drogamais = {
            "user": DB_CONFIG.get("user"),
            "password": DB_CONFIG.get("password"),
            "host": DB_CONFIG.get("host"),
            "port": DB_CONFIG.get("port", 3306), # Usa 3306 como padrão
            #"database": "dbDrogamais", # Define o banco de dados
            "database": "dbSults",
            "collation": "utf8mb4_general_ci"
        }

        if 'db_drogamais' not in g:
            # Conecta usando a configuração limpa
            g.db_drogamais = mysql.connector.connect(**config_drogamais)
        return g.db_drogamais
        
    except Error as e:
        print(f"Erro ao conectar ao dbDrogamais: {e}")
        return None

def close_drogamais_db_connection(e=None):
    """ Fecha a conexão específica do dbDrogamais """
    db = g.pop('db_drogamais', None)
    if db is not None:
        db.close()

def validate_gtins_in_external_db(gtin_list):

    if not gtin_list:
        return set(), None

    conn = get_drogamais_db_connection()
    if conn is None:
        return None, "Não foi possível conectar ao banco de dados dbDrogamais."

    cursor = conn.cursor()
    try:
        # Cria placeholders (%s) para a lista de GTINs
        format_strings = ','.join(['%s'] * len(gtin_list))
        
        sql = f"""
            SELECT codigo_barras AS gtin
            FROM bronze_plugpharma_produtos
            WHERE `codigo_barras` IN ({format_strings})
        """
        
        #params = tuple(gtin_list) + tuple(gtin_list)
        params = tuple(gtin_list)
        cursor.execute(sql, params)
        
        # Retorna um set (ex: {'789...', '789...'}) dos GTINs encontrados
        validos = {row[0] for row in cursor.fetchall()}
        return validos, None
        
    except Error as e:
        return None, str(e)
    finally:
        if cursor:
            cursor.close()