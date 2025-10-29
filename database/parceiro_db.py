# database/parceiro_db.py

from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError
from database.common_db import get_db_connection

DIM_PARCEIRO_TABLE = "bronze_parceiros"

def create_tables():
    conn = get_db_connection()
    if conn is None: return
    try:
        sql = text(f"""
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
                status INT DEFAULT 1,
                data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        conn.execute(sql)
        conn.commit()
    except SQLAlchemyError as e:
        print(f"Erro ao criar tabela {DIM_PARCEIRO_TABLE}: {e}")
        conn.rollback()

def add_parceiro(cnpj, nome_fantasia, tipo, razao_social, nome, email, telefone, data_entrada, data_saida, status):
    conn = get_db_connection()
    sql = text(f"""
        INSERT INTO {DIM_PARCEIRO_TABLE} (
            cnpj, nome_fantasia, tipo, razao_social, nome, 
            email, telefone, data_entrada, data_saida, status
        ) VALUES (:cnpj, :nome_fantasia, :tipo, :razao_social, :nome, 
            :email, :telefone, :data_entrada, :data_saida, :status)
    """)
    try:
        params = {
            "cnpj": cnpj, "nome_fantasia": nome_fantasia, "tipo": tipo, 
            "razao_social": razao_social, "nome": nome, "email": email, 
            "telefone": telefone, "data_entrada": data_entrada, 
            "data_saida": data_saida, "status": status
        }
        conn.execute(sql, params)
        conn.commit()
        return None
    except SQLAlchemyError as e:
        conn.rollback()
        return str(e)

def get_all_parceiros():
    conn = get_db_connection()
    sql = text(f"SELECT * FROM {DIM_PARCEIRO_TABLE} ORDER BY nome ASC")
    try:
        cursor = conn.execute(sql)
        results = cursor.mappings().fetchall()
        cursor.close()
        return results
    except SQLAlchemyError as e:
        print(f"Erro ao buscar parceiros: {e}")
        return []

def get_parceiro_by_id(parceiro_id):
    conn = get_db_connection()
    sql = text(f"SELECT * FROM {DIM_PARCEIRO_TABLE} WHERE id = :id")
    try:
        cursor = conn.execute(sql, {"id": parceiro_id})
        result = cursor.mappings().fetchone()
        cursor.close()
        return result
    except SQLAlchemyError as e:
        print(f"Erro ao buscar parceiro por id: {e}")
        return None

def update_parceiro(parceiro_id, cnpj, nome_fantasia, tipo, razao_social, nome, email, telefone, data_entrada, data_saida, status):
    conn = get_db_connection()
    sql = text(f"""
        UPDATE {DIM_PARCEIRO_TABLE} SET
            cnpj = :cnpj, nome_fantasia = :nome_fantasia, tipo = :tipo, 
            razao_social = :razao_social, nome = :nome, email = :email, 
            telefone = :telefone, data_entrada = :data_entrada, 
            data_saida = :data_saida, status = :status
        WHERE id = :id
    """)
    try:
        params = {
            "cnpj": cnpj, "nome_fantasia": nome_fantasia, "tipo": tipo, 
            "razao_social": razao_social, "nome": nome, "email": email, 
            "telefone": telefone, "data_entrada": data_entrada, 
            "data_saida": data_saida, "status": status, "id": parceiro_id
        }
        result = conn.execute(sql, params)
        conn.commit()
        return result.rowcount, None
    except SQLAlchemyError as e:
        conn.rollback()
        return 0, str(e)

def delete_parceiro(parceiro_id):
    conn = get_db_connection()
    sql = text(f"UPDATE {DIM_PARCEIRO_TABLE} SET status = 0 WHERE id = :id")
    try:
        result = conn.execute(sql, {"id": parceiro_id})
        conn.commit()
        return result.rowcount, None
    except SQLAlchemyError as e:
        conn.rollback()
        return 0, str(e)