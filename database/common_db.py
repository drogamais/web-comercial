# database/common_db.py

import mysql.connector
from mysql.connector import Error, pooling # 1. IMPORTAR POOLING
from flask import g
from config import DB_CONFIG # Precisa importar a configuração

# --- CRIAR O POOL PRINCIPAL ---
# (Usando a configuração padrão do config.py, que já aponta para dbDrogamais)
try:
    main_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="main_pool", # Nome genérico
        pool_size=10, # Talvez aumentar um pouco se for compartilhado
        **DB_CONFIG
    )
except Error as e:
    print(f"Erro ao criar o pool de conexões principal: {e}")
    main_pool = None
# --- FIM ---

# --- FUNÇÃO PRINCIPAL PARA OBTER CONEXÃO ---
def get_db_connection():
    """Obtém uma conexão do pool principal."""
    try:
        # Usar uma chave genérica em 'g'
        if 'db_conn' not in g:
            if main_pool is None:
                 raise Error("Pool de conexões 'main_pool' não está disponível.")
            g.db_conn = main_pool.get_connection()
        return g.db_conn
    except Error as e:
        print(f"Erro ao obter conexão do pool principal: {e}")
        return None
# --- FIM ---

# --- FUNÇÃO PRINCIPAL PARA FECHAR/DEVOLVER CONEXÃO ---
def close_db_connection(e=None):
    """Devolve a conexão principal ao pool."""
    db = g.pop('db_conn', None)
    if db is not None:
        db.close()
# --- FIM ---


def validate_gtins_in_external_db(gtin_list):
    """
    Valida uma lista de GTINs (espera-se que já estejam normalizados/padded).
    Retorna um SET de GTINs válidos.
    """
    if not gtin_list:
        return set(), None

    conn = get_db_connection()
    if conn is None:
        return None, "Não foi possível conectar ao banco de dados dbDrogamais."

    cursor = conn.cursor()
    try:
        # Cria placeholders (%s) para a lista de GTINs
        format_strings = ','.join(['%s'] * len(gtin_list))
        
        sql = f"""
            SELECT codigo_barras_normalizado AS gtin
            FROM bronze_plugpharma_produtos
            WHERE `codigo_barras_normalizado` IN ({format_strings})
        """
        
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

def get_codigo_interno_map_from_gtins(gtin_list):
    """
    Busca o codigo_interno para uma lista de GTINs (espera-se que já estejam normalizados/padded).
    Retorna um DICIONÁRIO {gtin_normalizado: codigo_interno}.
    """
    if not gtin_list:
        return {}, None

    conn = get_db_connection()
    if conn is None:
        return None, "Não foi possível conectar ao banco de dados dbDrogamais."

    cursor = conn.cursor()
    try:
        format_strings = ','.join(['%s'] * len(gtin_list))
        
        # Seleciona o gtin normalizado e o codigo_interno
        sql = f"""
            SELECT codigo_barras_normalizado, codigo_interno
            FROM bronze_plugpharma_produtos
            WHERE `codigo_barras_normalizado` IN ({format_strings})
        """
        
        params = tuple(gtin_list)
        cursor.execute(sql, params)
        
        # Retorna um dicionário (ex: {'00789...': '12345', '00789...': '67890'})
        validos_map = {row[0]: row[1] for row in cursor.fetchall()}
        return validos_map, None
        
    except Error as e:
        return None, str(e)
    finally:
        if cursor:
            cursor.close()