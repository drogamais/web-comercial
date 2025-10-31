# database/tabloide_db.py

from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError
from database.common_db import get_db_connection
import datetime

DIM_TABLOIDE_TABLE = "dim_tabloide"

def create_tables():
    conn = get_db_connection()
    if conn is None: return
    try:
        sql = text(f"""
            CREATE TABLE IF NOT EXISTS {DIM_TABLOIDE_TABLE} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                data_inicio DATE NOT NULL,
                data_fim DATE NOT NULL,
                status INT DEFAULT 1,
                data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE(nome, data_inicio, data_fim)
            )
        """)
        conn.execute(sql)
        conn.commit()
    except SQLAlchemyError as e:
        print(f"Erro ao criar tabela {DIM_TABLOIDE_TABLE} (Tabloide): {e}")
        conn.rollback()

def add_tabloide(nome, data_inicio, data_fim):
    conn = get_db_connection()
    sql = text(f"""
        INSERT INTO {DIM_TABLOIDE_TABLE} (nome, data_inicio, data_fim, status) 
        VALUES (:nome, :data_inicio, :data_fim, 1)
    """)
    try:
        params = {"nome": nome, "data_inicio": data_inicio, "data_fim": data_fim}
        conn.execute(sql, params)
        conn.commit()
        return None
    except SQLAlchemyError as e:
        conn.rollback()
        return str(e)

def get_all_tabloide():
    conn = get_db_connection()
    sql = text(f"SELECT * FROM {DIM_TABLOIDE_TABLE} WHERE status = 1 ORDER BY data_inicio DESC")
    try:
        cursor = conn.execute(sql)
        results = cursor.mappings().fetchall()
        cursor.close()
        return results
    except SQLAlchemyError as e:
        print(f"Erro ao buscar tabloides: {e}")
        return []

def get_active_tabloide_for_upload():
    conn = get_db_connection()
    if conn is None: return []
    today = datetime.date.today()
    sql = text(f"""
        SELECT * FROM {DIM_TABLOIDE_TABLE} 
        WHERE data_fim >= :today 
        ORDER BY data_inicio DESC
    """)
    try:
        cursor = conn.execute(sql, {"today": today})
        results = cursor.mappings().fetchall()
        cursor.close()
        return results
    except SQLAlchemyError as e:
        print(f"Erro ao buscar {DIM_TABLOIDE_TABLE} ativos para upload: {e}")
        return []

def get_tabloide_by_id(tabloide_id):
    conn = get_db_connection()
    sql = text(f"SELECT * FROM {DIM_TABLOIDE_TABLE} WHERE id = :id")
    try:
        cursor = conn.execute(sql, {"id": tabloide_id})
        result = cursor.mappings().fetchone()
        cursor.close()
        return result
    except SQLAlchemyError as e:
        print(f"Erro ao buscar tabloide por id: {e}")
        return None

def update_tabloide(tabloide_id, nome, data_inicio, data_fim):
    conn = get_db_connection()
    sql = text(f"""
        UPDATE {DIM_TABLOIDE_TABLE} SET nome = :nome, data_inicio = :data_inicio, data_fim = :data_fim
        WHERE id = :id
    """)
    try:
        params = {"nome": nome, "data_inicio": data_inicio, "data_fim": data_fim, "id": tabloide_id}
        result = conn.execute(sql, params)
        conn.commit()
        return result.rowcount, None
    except SQLAlchemyError as e:
        conn.rollback()
        return 0, str(e)

#####################
# HARD DELETE
#####################
def delete_tabloide(tabloide_id):
    conn = get_db_connection()
    sql = text(f"DELETE FROM {DIM_TABLOIDE_TABLE} WHERE id = :id")
    try:
        result = conn.execute(sql, {"id": tabloide_id})
        conn.commit()
        return result.rowcount, None
    except SQLAlchemyError as e:
        conn.rollback()
        return 0, str(e)

# #####################
# # SOFT DELETE
# #####################
# def delete_tabloide(tabloide_id):
#     conn = get_db_connection()
#     sql = text(f"UPDATE {DIM_TABLOIDE_TABLE} SET status = 0 WHERE id = :id")
#     try:
#         result = conn.execute(sql, {"id": tabloide_id})
#         conn.commit()
#         return result.rowcount, None
#     except SQLAlchemyError as e:
#         conn.rollback()
#         return 0, str(e)