import mysql.connector
from mysql.connector import Error
from flask import g
from config import DB_CONFIG

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
    conn = get_db_connection()
    if conn is None: return
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parceiros (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                status INT DEFAULT 1,  -- 1 = Ativo, 0 = Inativo
                UNIQUE(nome)
            )
        """)
        conn.commit()
    except Error as e:
        print(f"Erro ao criar tabela parceiros: {e}")
    finally:
        cursor.close()

def add_parceiro(nome):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO parceiros (nome, status) VALUES (%s, 1)", (nome,))
        conn.commit()
        return None
    except Error as e:
        conn.rollback()
        return str(e)
    finally:
        cursor.close()

def get_all_parceiros():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM parceiros WHERE status = 1 ORDER BY nome ASC")
    return cursor.fetchall()

def get_parceiro_by_id(parceiro_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM parceiros WHERE id = %s", (parceiro_id,))
    return cursor.fetchone()

def update_parceiro(parceiro_id, nome):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "UPDATE parceiros SET nome = %s WHERE id = %s"
    try:
        cursor.execute(sql, (nome, parceiro_id))
        conn.commit()
        return cursor.rowcount, None
    except Error as e:
        conn.rollback()
        return 0, str(e)
    finally:
        cursor.close()

def delete_parceiro(parceiro_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "UPDATE parceiros SET status = 0 WHERE id = %s"
    try:
        cursor.execute(sql, (parceiro_id,))
        conn.commit()
        return cursor.rowcount, None
    except Error as e:
        conn.rollback()
        return 0, str(e)
    finally:
        cursor.close()