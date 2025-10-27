# database/tabloide_produtos_db.py

from mysql.connector import Error
from database.common_db import get_db_connection

DIM_TABLOIDE_TABLE = "dim_tabloide"
DIM_TABLOIDE_PRODUTO_TABLE = "dim_tabloide_produto"

def create_product_table():
    """ Cria APENAS a tabela dim_tabloide_produto """
    conn = get_db_connection()
    if conn is None: return
    cursor = conn.cursor()
    try:
        # Tabela 'produtos_tabloide' (Schema ATUALIZADO)
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {DIM_TABLOIDE_PRODUTO_TABLE} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                campanha_id INT NOT NULL,
                codigo_barras VARCHAR(14),
                codigo_barras_normalizado VARCHAR(14) DEFAULT NULL,
                codigo_interno VARCHAR(14) DEFAULT NULL,
                descricao TEXT,

                laboratorio VARCHAR(255),
                tipo_preco VARCHAR(100) DEFAULT NULL,
                preco_normal DECIMAL(10, 2),
                preco_desconto DECIMAL(10, 2),
                preco_desconto_cliente DECIMAL(10, 2),
                preco_app DECIMAL(10, 2),
                tipo_regra VARCHAR(100),
                data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

                FOREIGN KEY (campanha_id) REFERENCES {DIM_TABLOIDE_TABLE}(id) ON DELETE CASCADE
            )
        """)
        # --- Adicionar coluna se não existir (para bancos já criados) ---
        cursor.execute(f"""
            ALTER TABLE {DIM_TABLOIDE_PRODUTO_TABLE}
            ADD COLUMN IF NOT EXISTS codigo_barras_normalizado VARCHAR(14) DEFAULT NULL
            AFTER codigo_barras;
        """)
        # -----------------------------------------------------------------
        conn.commit()
    except Error as e:
        print(f"Erro ao criar/alterar tabela {DIM_TABLOIDE_PRODUTO_TABLE} (Tabloide): {e}")
    finally:
        cursor.close()

#####################################
#       TABLOIDE PRODUTOS
#####################################
def add_products_bulk(produtos):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = f"""
        INSERT INTO {DIM_TABLOIDE_PRODUTO_TABLE} (
            campanha_id, codigo_barras, codigo_barras_normalizado, codigo_interno, descricao, laboratorio,
            tipo_preco, preco_normal, preco_desconto, preco_desconto_cliente, preco_app, tipo_regra
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
    cursor.execute(f"""SELECT * FROM {DIM_TABLOIDE_PRODUTO_TABLE} WHERE campanha_id = %s""", (campanha_id,))
    return cursor.fetchall()

def add_single_product(dados_produto):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = f"""
        INSERT INTO {DIM_TABLOIDE_PRODUTO_TABLE} (
            campanha_id, codigo_barras, codigo_barras_normalizado, codigo_interno, descricao, laboratorio,
            tipo_preco, preco_normal, preco_desconto, preco_desconto_cliente, preco_app, tipo_regra
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
    sql = f"""
        UPDATE {DIM_TABLOIDE_PRODUTO_TABLE} SET
            codigo_barras = %s, codigo_barras_normalizado = %s, codigo_interno = %s, descricao = %s, laboratorio = %s,
            tipo_preco = %s, preco_normal = %s, preco_desconto = %s, preco_desconto_cliente = %s, preco_app = %s, tipo_regra = %s
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
    if not ids_para_deletar:
        return 0, None
    cursor = conn.cursor()
    format_strings = ','.join(['%s'] * len(ids_para_deletar))
    sql = f"""DELETE FROM {DIM_TABLOIDE_PRODUTO_TABLE} WHERE id IN ({format_strings})"""
    try:
        cursor.execute(sql, tuple(ids_para_deletar))
        conn.commit()
        return cursor.rowcount, None
    except Error as e:
        conn.rollback()
        return 0, str(e)
    finally:
        cursor.close()

def delete_products_by_campaign_id(campanha_id):
    """Deleta TODOS os produtos associados a um campanha_id (que é o ID do tabloide aqui)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = f"""
        DELETE FROM {DIM_TABLOIDE_PRODUTO_TABLE} WHERE campanha_id = %s
    """
    try:
        cursor.execute(sql, (campanha_id,))
        conn.commit()
        return cursor.rowcount, None # Retorna número de linhas deletadas e None (sem erro)
    except Error as e:
        conn.rollback()
        return 0, str(e) # Retorna 0 linhas e a mensagem de erro
    finally:
        cursor.close()