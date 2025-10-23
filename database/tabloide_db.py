# aplicacao_web_campanhas/database_tabloide.py

import mysql.connector
from mysql.connector import Error
from flask import g
from config import DB_CONFIG
import datetime

DIM_TABLOIDE_TABLE = "dim_tabloide"
FAT_PRODUTO_TABLE = "fat_tabloide_produto"

def get_db_connection():
    try:
        if 'db_tabloide' not in g: # Nome único para a conexão
            g.db_tabloide = mysql.connector.connect(**DB_CONFIG)
        return g.db_tabloide
    except Error as e:
        print(f"Erro ao conectar ao MySQL (Tabloide): {e}")
        return None

def close_db_connection(e=None):
    db = g.pop('db_tabloide', None)
    if db is not None:
        db.close()

def create_tables():
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
        # Tabela 'produtos_tabloide' (Schema ATUALIZADO)
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {FAT_PRODUTO_TABLE} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                campanha_id INT NOT NULL,
                codigo_barras VARCHAR(50),
                descricao VARCHAR(255),
                
                -- Colunas da planilha
                laboratorio VARCHAR(255),
                preco_normal DECIMAL(10, 2),
                preco_desconto DECIMAL(10, 2),      -- (PREÇO DESCONTO GERAL)
                preco_desconto_cliente DECIMAL(10, 2),
                tipo_regra VARCHAR(100),
                
                -- Colunas antigas (mantidas como NULLable, mas não usadas)
                pontuacao INT,
                rebaixe DECIMAL(10, 2),
                qtd_limite INT,

                FOREIGN KEY (campanha_id) REFERENCES {DIM_TABLOIDE_TABLE}(id) ON DELETE CASCADE
            )
        """)
        conn.commit()
    except Error as e:
        print(f"Erro ao criar tabelas (Tabloide): {e}")
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


#####################################
#       TABLOIDE PRODUTOS
#####################################
def add_products_bulk(produtos):
    conn = get_db_connection()
    cursor = conn.cursor()
    # SQL ATUALIZADO
    sql = f"""
        INSERT INTO {FAT_PRODUTO_TABLE} (
            campanha_id, codigo_barras, descricao, laboratorio, 
            preco_normal, preco_desconto, preco_desconto_cliente, tipo_regra
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        cursor.executemany(sql, produtos)
        conn.commit()
        return cursor.rowcount, None
    except Error as e:
        conn.rollback()
        return 0, str(e)
    finally:
        cursor.close()

def get_products_by_campaign_id(campanha_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"""SELECT * FROM {FAT_PRODUTO_TABLE} WHERE campanha_id = %s""", (campanha_id,))
    return cursor.fetchall()

def add_single_product(dados_produto):
    conn = get_db_connection()
    cursor = conn.cursor()
    # SQL ATUALIZADO
    sql = f"""
        INSERT INTO {FAT_PRODUTO_TABLE} (
            campanha_id, codigo_barras, descricao, laboratorio, 
            preco_normal, preco_desconto, preco_desconto_cliente, tipo_regra
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        cursor.execute(sql, dados_produto)
        conn.commit()
        return cursor.rowcount, None
    except Error as e:
        conn.rollback()
        return 0, str(e)
    finally:
        cursor.close()

def update_products_in_bulk(produtos_para_atualizar):
    conn = get_db_connection()
    cursor = conn.cursor()
    # SQL ATUALIZADO
    sql = f"""
        UPDATE {FAT_PRODUTO_TABLE} SET
            codigo_barras = %s, descricao = %s, laboratorio = %s, preco_normal = %s, 
            preco_desconto = %s, preco_desconto_cliente = %s, tipo_regra = %s
        WHERE id = %s
    """
    try:
        cursor.executemany(sql, produtos_para_atualizar)
        conn.commit()
        return cursor.rowcount, None
    except Error as e:
        conn.rollback()
        return 0, str(e)
    finally:
        cursor.close()

def delete_products_in_bulk(ids_para_deletar):
    conn = get_db_connection()
    cursor = conn.cursor()
    format_strings = ','.join(['%s'] * len(ids_para_deletar))
    sql = f"""DELETE FROM {FAT_PRODUTO_TABLE} WHERE id IN ({format_strings})"""
    try:
        cursor.execute(sql, tuple(ids_para_deletar))
        conn.commit()
        return cursor.rowcount, None
    except Error as e:
        conn.rollback()
        return 0, str(e)
    finally:
        cursor.close()