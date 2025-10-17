# aplicacao_web_campanhas/database_campanha.py

import mysql.connector
from mysql.connector import Error
from flask import g
from config import DB_CONFIG

def get_db_connection():
    try:
        if 'db' not in g:
            g.db = mysql.connector.connect(**DB_CONFIG)
        return g.db
    except Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
        return None

def close_db_connection(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def create_tables():
    conn = get_db_connection()
    if conn is None: return
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campanhas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                data_inicio DATE NOT NULL,
                data_fim DATE NOT NULL,
                UNIQUE(nome)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                campanha_id INT NOT NULL,
                codigo_barras VARCHAR(50),
                descricao VARCHAR(255),
                pontuacao INT,
                preco_normal DECIMAL(10, 2),
                preco_desconto DECIMAL(10, 2),
                rebaixe DECIMAL(10, 2),
                qtd_limite INT,
                FOREIGN KEY (campanha_id) REFERENCES campanhas(id) ON DELETE CASCADE
            )
        """)
        conn.commit()
    except Error as e:
        print(f"Erro ao criar tabelas: {e}")
    finally:
        cursor.close()

def add_campaign(nome, data_inicio, data_fim):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO campanhas (nome, data_inicio, data_fim) VALUES (%s, %s, %s)",
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
    cursor.execute("SELECT * FROM campanhas ORDER BY data_inicio DESC")
    return cursor.fetchall()

def get_campaign_by_id(campanha_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM campanhas WHERE id = %s", (campanha_id,))
    return cursor.fetchone()

def update_campaign(campaign_id, nome, data_inicio, data_fim):
    """Atualiza os dados de uma campanha existente."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """
        UPDATE campanhas SET nome = %s, data_inicio = %s, data_fim = %s
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
    """Deleta uma campanha e todos os produtos associados (devido ao ON DELETE CASCADE)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "DELETE FROM campanhas WHERE id = %s"
    try:
        cursor.execute(sql, (campaign_id,))
        conn.commit()
        return cursor.rowcount, None
    except Error as e:
        conn.rollback()
        return 0, str(e)
    finally:
        cursor.close()

def add_products_bulk(produtos):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """
        INSERT INTO produtos (campanha_id, codigo_barras, descricao, pontuacao, preco_normal, preco_desconto, rebaixe, qtd_limite)
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
    cursor.execute("SELECT * FROM produtos WHERE campanha_id = %s", (campanha_id,))
    return cursor.fetchall()

def add_single_product(dados_produto):
    """Adiciona um único produto ao banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """
        INSERT INTO produtos (campanha_id, codigo_barras, descricao, pontuacao, preco_normal, preco_desconto, rebaixe, qtd_limite)
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
    """Atualiza múltiplos produtos no banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """
        UPDATE produtos SET
            codigo_barras = %s, descricao = %s, pontuacao = %s,
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
    # Prepara a query para aceitar uma lista de IDs
    format_strings = ','.join(['%s'] * len(ids_para_deletar))
    sql = f"DELETE FROM produtos WHERE id IN ({format_strings})"
    try:
        cursor.execute(sql, tuple(ids_para_deletar))
        conn.commit()
        return cursor.rowcount, None
    except Error as e:
        conn.rollback()
        return 0, str(e)
    finally:
        cursor.close()