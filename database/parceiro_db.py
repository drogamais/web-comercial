import mysql.connector
from mysql.connector import Error
from flask import g
from config import DB_CONFIG

DIM_PARCEIRO_TABLE = "bronze_parceiros"

def get_db_connection():
    try:
        if 'db_parceiro' not in g: # Nome único
            g.db_parceiro = mysql.connector.connect(**DB_CONFIG)
        return g.db_parceiro
    except Error as e:
        print(f"Erro ao conectar ao MySQL (Parceiro): {e}")
        return None

def close_db_connection(e=None):
    db = g.pop('db_parceiro', None)
    if db is not None:
        db.close()

def create_tables():
    """
    Cria a tabela dim_parceiro com a nova estrutura completa.
    """
    conn = get_db_connection()
    if conn is None: return
    cursor = conn.cursor()
    try:
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {DIM_PARCEIRO_TABLE} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                tipo VARCHAR(100) DEFAULT NULL,
                cnpj VARCHAR(18) DEFAULT NULL,
                nome_fantasia VARCHAR(255) DEFAULT NULL,
                razao_social VARCHAR(255) DEFAULT NULL,
                email VARCHAR(255) DEFAULT NULL,
                telefone VARCHAR(20) DEFAULT NULL,
                data_entrada DATE DEFAULT NULL,
                data_saida DATE DEFAULT NULL,
                status INT DEFAULT 1
            )
        """)
        conn.commit()
    except Error as e:
        print(f"Erro ao criar tabela {DIM_PARCEIRO_TABLE}: {e}")
    finally:
        cursor.close()

def add_parceiro(cnpj, nome_fantasia, tipo, razao_social, nome, email, telefone, data_entrada, data_saida, status):
    """
    Adiciona um novo parceiro com todos os campos.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = f"""
        INSERT INTO {DIM_PARCEIRO_TABLE} (
            cnpj, nome_fantasia, tipo, razao_social, nome, 
            email, telefone, data_entrada, data_saida, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        cursor.execute(sql, (
            cnpj, nome_fantasia, tipo, razao_social, nome,
            email, telefone, data_entrada, data_saida, status
        ))
        conn.commit()
        return None
    except Error as e:
        conn.rollback()
        return str(e)
    finally:
        cursor.close()

def get_all_parceiros():
    """
    Busca todos os parceiros (ativos e inativos) para a gestão.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # Atualizado para ordenar pelo novo campo 'nome'
    cursor.execute(f"""SELECT * FROM {DIM_PARCEIRO_TABLE} ORDER BY nome ASC""")
    return cursor.fetchall()

def get_parceiro_by_id(parceiro_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"""SELECT * FROM {DIM_PARCEIRO_TABLE} WHERE id = %s""", (parceiro_id,))
    return cursor.fetchone()

def update_parceiro(parceiro_id, cnpj, nome_fantasia, tipo, razao_social, nome, email, telefone, data_entrada, data_saida, status):
    """
    Atualiza um parceiro existente com todos os campos.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = f"""
        UPDATE {DIM_PARCEIRO_TABLE} SET
            cnpj = %s, nome_fantasia = %s, tipo = %s, razao_social = %s, 
            nome = %s, email = %s, telefone = %s, data_entrada = %s, 
            data_saida = %s, status = %s
        WHERE id = %s
    """
    try:
        cursor.execute(sql, (
            cnpj, nome_fantasia, tipo, razao_social, nome,
            email, telefone, data_entrada, data_saida, status,
            parceiro_id
        ))
        conn.commit()
        return cursor.rowcount, None
    except Error as e:
        conn.rollback()
        return 0, str(e)
    finally:
        cursor.close()

def delete_parceiro(parceiro_id):
    """
    Realiza um "soft delete" (apenas marca como inativo).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    # A lógica de soft-delete é mantida, apenas atualiza o status.
    sql = f"""UPDATE {DIM_PARCEIRO_TABLE} SET status = 0 WHERE id = %s"""
    try:
        cursor.execute(sql, (parceiro_id,))
        conn.commit()
        return cursor.rowcount, None
    except Error as e:
        conn.rollback()
        return 0, str(e)
    finally:
        cursor.close()