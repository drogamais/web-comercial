# database/tabloide_db.py

import mysql.connector
from mysql.connector import Error
from flask import g
from config import DB_CONFIG
import datetime

DIM_TABLOIDE_TABLE = "dim_tabloide"
# FAT_PRODUTO_TABLE foi movido para tabloide_produtos_db.py

def get_db_connection():
    """
    Obtém a conexão do banco de dados para o módulo TABLOIDE.
    Esta conexão (g.db_tabloide) será usada por tabloide_db e tabloide_produtos_db.
    """
    try:
        if 'db_tabloide' not in g: # Nome único para a conexão
            g.db_tabloide = mysql.connector.connect(**DB_CONFIG)
        return g.db_tabloide
    except Error as e:
        print(f"Erro ao conectar ao MySQL (Tabloide): {e}")
        return None

def close_db_connection(e=None):
    """ Fecha a conexão do módulo TABLOIDE (g.db_tabloide) """
    db = g.pop('db_tabloide', None)
    if db is not None:
        db.close()

def create_tables():
    """ Cria APENAS a tabela dim_tabloide """
    conn = get_db_connection()
    if conn is None: return
    cursor = conn.cursor()
    try:
        # Tabela 'tabloides'
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {DIM_TABLOIDE_TABLE} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                data_inicio DATE NOT NULL,
                data_fim DATE NOT NULL,
                status INT DEFAULT 1,
                UNIQUE(nome)
            )
        """)
        conn.commit()
    except Error as e:
        print(f"Erro ao criar tabela {DIM_TABLOIDE_TABLE} (Tabloide): {e}")
    finally:
        cursor.close()

#####################################
#            TABLOIDE
#####################################

def add_campaign(nome, data_inicio, data_fim):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"""INSERT INTO {DIM_TABLOIDE_TABLE} (nome, data_inicio, data_fim, status) VALUES (%s, %s, %s, 1)""",
                       (nome, data_inicio, data_fim))
        conn.commit()
        return None
    except Error as e:
        conn.rollback()
        return str(e)
    finally:
        cursor.close()

def get_all_campaigns():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"""SELECT * FROM {DIM_TABLOIDE_TABLE} WHERE status = 1 ORDER BY data_inicio DESC""")
    return cursor.fetchall()

def get_active_campaigns_for_upload():
    conn = get_db_connection()
    if conn is None: return []
    cursor = conn.cursor(dictionary=True)
    today = datetime.date.today()
    try:
        cursor.execute(
            f"""SELECT * FROM {DIM_TABLOIDE_TABLE} WHERE status = 1 AND data_fim >= %s ORDER BY data_inicio DESC""",
            (today,)
        )
        return cursor.fetchall()
    except Error as e:
        print(f"""Erro ao buscar {DIM_TABLOIDE_TABLE} ativos para upload: {e}""")
        return []
    finally:
        cursor.close()

def get_campaign_by_id(campanha_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"""SELECT * FROM {DIM_TABLOIDE_TABLE} WHERE id = %s""", (campanha_id,))
    return cursor.fetchone()

def update_campaign(campaign_id, nome, data_inicio, data_fim):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = f"""UPDATE {DIM_TABLOIDE_TABLE} SET nome = %s, data_inicio = %s, data_fim = %s WHERE id = %s"""
    try:
        cursor.execute(sql, (nome, data_inicio, data_fim, campaign_id))
        conn.commit()
        return cursor.rowcount, None
    except Error as e:
        conn.rollback()
        return 0, str(e)
    finally:
        cursor.close()

def delete_campaign(campaign_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = f"""UPDATE {DIM_TABLOIDE_TABLE} SET status = 0 WHERE id = %s"""
    try:
        cursor.execute(sql, (campaign_id,))
        conn.commit()
        return cursor.rowcount, None
    except Error as e:
        conn.rollback()
        return 0, str(e)
    finally:
        cursor.close()

# Todas as funções de PRODUTO foram movidas