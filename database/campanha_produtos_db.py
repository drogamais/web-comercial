# database/campanha_produtos_db.py

from mysql.connector import Error
# Importa a conexão do módulo principal de campanha
from database.campanha_db import get_db_connection

DIM_CAMPANHA_TABLE = "dim_campanha"
FAT_PRODUTO_TABLE = "fat_campanha_produto"

def create_product_table():
    """ Cria APENAS a tabela fat_campanha_produto """
    conn = get_db_connection()
    if conn is None: return
    cursor = conn.cursor()
    try:
        sql_create_fact = f"""
            CREATE TABLE IF NOT EXISTS {FAT_PRODUTO_TABLE} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                campanha_id INT NOT NULL,
                codigo_barras VARCHAR(50),
                codigo_interno VARCHAR(50) DEFAULT NULL,
                descricao VARCHAR(255),
                pontuacao INT,
                preco_normal DECIMAL(10, 2),
                preco_desconto DECIMAL(10, 2),
                rebaixe DECIMAL(10, 2),
                qtd_limite INT,
                data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (campanha_id) REFERENCES {DIM_CAMPANHA_TABLE}(id) ON DELETE CASCADE
            )
        """
        cursor.execute(sql_create_fact)
        conn.commit()
    except Error as e:
        print(f"Erro ao criar tabela {FAT_PRODUTO_TABLE}: {e}")
    finally:
        cursor.close()

#############################################
##          PRODUTOS CAMPANHA
#############################################

def add_products_bulk(produtos):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = f"""
        INSERT INTO {FAT_PRODUTO_TABLE} (
            campanha_id, codigo_barras, codigo_interno, descricao, pontuacao, 
            preco_normal, preco_desconto, rebaixe, qtd_limite
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
    """Adiciona um único produto ao banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = f"""
        INSERT INTO {FAT_PRODUTO_TABLE} (
            campanha_id, codigo_barras, codigo_interno, descricao, pontuacao, 
            preco_normal, preco_desconto, rebaixe, qtd_limite
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
    """Atualiza múltiplos produtos no banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = f"""
        UPDATE {FAT_PRODUTO_TABLE} SET
            codigo_barras = %s, codigo_interno = %s, descricao = %s, pontuacao = %s,
            preco_normal = %s, preco_desconto = %s, rebaixe = %s, qtd_limite = %s
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
    """Deleta múltiplos produtos do banco de dados com base em seus IDs."""
    conn = get_db_connection()
    cursor = conn.cursor()
    format_strings = ','.join(['%s'] * len(ids_para_deletar))
    sql = f"""
        DELETE FROM {FAT_PRODUTO_TABLE} WHERE id IN ({format_strings})
    """
    try:
        cursor.execute(sql, tuple(ids_para_deletar))
        conn.commit()
        return cursor.rowcount, None
    except Error as e:
        conn.rollback()
        return 0, str(e)
    finally:
        cursor.close()