# database/tabloide_produtos_db.py

from mysql.connector import Error
# Importa a conexão do módulo principal de tabloide
from database.tabloide_db import get_db_connection

DIM_TABLOIDE_TABLE = "dim_tabloide"
FAT_PRODUTO_TABLE = "fat_tabloide_produto"

def create_product_table():
    """ Cria APENAS a tabela fat_tabloide_produto """
    conn = get_db_connection()
    if conn is None: return
    cursor = conn.cursor()
    try:
        # Tabela 'produtos_tabloide' (Schema ATUALIZADO)
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {FAT_PRODUTO_TABLE} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                campanha_id INT NOT NULL,
                codigo_barras VARCHAR(50),
                codigo_interno VARCHAR(50) DEFAULT NULL,
                descricao VARCHAR(255),
                
                laboratorio VARCHAR(255),
                preco_normal DECIMAL(10, 2),
                preco_desconto DECIMAL(10, 2),
                preco_desconto_cliente DECIMAL(10, 2),
                preco_app DECIMAL(10, 2),
                tipo_regra VARCHAR(100),
                data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

                FOREIGN KEY (campanha_id) REFERENCES {DIM_TABLOIDE_TABLE}(id) ON DELETE CASCADE
            )
        """)
        conn.commit()
    except Error as e:
        print(f"Erro ao criar tabela {FAT_PRODUTO_TABLE} (Tabloide): {e}")
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
            campanha_id, codigo_barras, codigo_interno, descricao, laboratorio, 
            preco_normal, preco_desconto, preco_desconto_cliente, preco_app, tipo_regra
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            campanha_id, codigo_barras, codigo_interno, descricao, laboratorio, 
            preco_normal, preco_desconto, preco_desconto_cliente, preco_app, tipo_regra
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            codigo_barras = %s, codigo_interno = %s, descricao = %s, laboratorio = %s, 
            preco_normal = %s, preco_desconto = %s, preco_desconto_cliente = %s, preco_app = %s, tipo_regra = %s
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