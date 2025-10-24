# database/campanha_db.py

import mysql.connector
from mysql.connector import Error
from flask import g
from config import DB_CONFIG
import datetime

DIM_CAMPANHA_TABLE = "dim_campanha"
# FAT_PRODUTO_TABLE foi movido para campanha_produtos_db.py

def get_db_connection():
    """
    Obtém a conexão do banco de dados para o módulo CAMPANHA.
    Esta conexão (g.db) será usada por campanha_db e campanha_produtos_db.
    """
    try:
        if 'db' not in g:
            g.db = mysql.connector.connect(**DB_CONFIG)
        return g.db
    except Error as e:
        print(f"Erro ao conectar ao MySQL (Campanha): {e}")
        return None

def close_db_connection(e=None):
    """ Fecha a conexão do módulo CAMPANHA (g.db) """
    db = g.pop('db', None)
    if db is not None:
        db.close()

def create_tables():
    """ Cria APENAS a tabela dim_campanha """
    conn = get_db_connection()
    if conn is None: return
    cursor = conn.cursor()
    try:
        sql_create_dim = f"""
            CREATE TABLE IF NOT EXISTS {DIM_CAMPANHA_TABLE} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                data_inicio DATE NOT NULL,
                data_fim DATE NOT NULL,
                status INT DEFAULT 1,
                data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                UNIQUE(nome)
            )
        """
        cursor.execute(sql_create_dim)
        conn.commit()
    except Error as e:
        print(f"Erro ao criar tabela {DIM_CAMPANHA_TABLE}: {e}")
    finally:
        cursor.close()

#############################################
##                  CAMPANHA
#############################################

def add_campaign(nome, data_inicio, data_fim):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = f"""
        INSERT INTO {DIM_CAMPANHA_TABLE} (nome, data_inicio, data_fim, status) VALUES (%s, %s, %s, 1)
    """
    try:
        cursor.execute(sql, (nome, data_inicio, data_fim))
        conn.commit()
        return None
    except Error as e:
        conn.rollback()
        return str(e)
    finally:
        cursor.close()

def get_all_campaigns():
    """Busca todas as campanhas ATIVAS (status=1)."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = f"""
        SELECT * FROM {DIM_CAMPANHA_TABLE} WHERE status = 1 ORDER BY data_inicio DESC
    """
    cursor.execute(sql)
    return cursor.fetchall()

def get_active_campaigns_for_upload():
    """
    Busca campanhas ativas (status=1) e que ainda não expiraram (data_fim >= hoje).
    Usado na página de Upload.
    """
    conn = get_db_connection()
    if conn is None: return []
    cursor = conn.cursor(dictionary=True)
    today = datetime.date.today()
    try:
        sql = f"""
            SELECT * FROM {DIM_CAMPANHA_TABLE} WHERE status = 1 AND data_fim >= %s ORDER BY data_inicio DESC
        """
        cursor.execute(sql,(today,))
        return cursor.fetchall()
    except Error as e:
        print(f"Erro ao buscar campanhas ativas para upload: {e}")
        return []
    finally:
        cursor.close()


def get_campaign_by_id(campanha_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = f"""
        SELECT * FROM {DIM_CAMPANHA_TABLE} WHERE id = %s
    """
    cursor.execute(sql, (campanha_id,))
    return cursor.fetchone()

def update_campaign(campaign_id, nome, data_inicio, data_fim):
    """Atualiza os dados de uma campanha existente."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = f"""
        UPDATE {DIM_CAMPANHA_TABLE} SET nome = %s, data_inicio = %s, data_fim = %s
        WHERE id = %s
    """
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
    """Realiza um soft delete de uma campanha (define status = 0)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = f"""
        UPDATE {DIM_CAMPANHA_TABLE} SET status = 0 WHERE id = %s
    """
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