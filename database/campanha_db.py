# database/campanha_db.py

from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError
from database.common_db import get_db_connection
import datetime

DIM_CAMPANHA_TABLE = "dim_campanha"

def create_tables():
    conn = get_db_connection()
    if conn is None: return
    try:
        sql = text(f"""
            CREATE TABLE IF NOT EXISTS {DIM_CAMPANHA_TABLE} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                data_inicio DATE NOT NULL,
                data_fim DATE NOT NULL,
                status INT DEFAULT 1,
                data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE(nome)
            )
        """)
        conn.execute(sql)
        conn.commit()
    except SQLAlchemyError as e:
        print(f"Erro ao criar tabela {DIM_CAMPANHA_TABLE}: {e}")
        conn.rollback()

def add_campaign(nome, data_inicio, data_fim):
    conn = get_db_connection()
    sql = text(f"""
        INSERT INTO {DIM_CAMPANHA_TABLE} (nome, data_inicio, data_fim, status) 
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

def get_all_campaigns():
    conn = get_db_connection()
    sql = text(f"SELECT * FROM {DIM_CAMPANHA_TABLE} WHERE status = 1 ORDER BY data_inicio DESC")
    try:
        cursor = conn.execute(sql)
        results = cursor.mappings().fetchall()
        cursor.close()
        return results
    except SQLAlchemyError as e:
        print(f"Erro ao buscar campanhas: {e}")
        return []

def get_active_campaigns_for_upload():
    conn = get_db_connection()
    if conn is None: return []
    today = datetime.date.today()
    sql = text(f"""
        SELECT * FROM {DIM_CAMPANHA_TABLE} 
        WHERE status = 1 AND data_fim >= :today 
        ORDER BY data_inicio DESC
    """)
    try:
        cursor = conn.execute(sql, {"today": today})
        results = cursor.mappings().fetchall()
        cursor.close()
        return results
    except SQLAlchemyError as e:
        print(f"Erro ao buscar campanhas ativas para upload: {e}")
        return []

def get_campaign_by_id(campanha_id):
    conn = get_db_connection()
    sql = text(f"SELECT * FROM {DIM_CAMPANHA_TABLE} WHERE id = :id")
    try:
        cursor = conn.execute(sql, {"id": campanha_id})
        result = cursor.mappings().fetchone()
        cursor.close()
        return result
    except SQLAlchemyError as e:
        print(f"Erro ao buscar campanha por id: {e}")
        return None

def update_campaign(campaign_id, nome, data_inicio, data_fim):
    conn = get_db_connection()
    sql = text(f"""
        UPDATE {DIM_CAMPANHA_TABLE} SET nome = :nome, data_inicio = :data_inicio, data_fim = :data_fim
        WHERE id = :id
    """)
    try:
        params = {"nome": nome, "data_inicio": data_inicio, "data_fim": data_fim, "id": campaign_id}
        result = conn.execute(sql, params)
        conn.commit()
        return result.rowcount, None
    except SQLAlchemyError as e:
        conn.rollback()
        return 0, str(e)

# #####################
# # DELETE PERMANENTE
# #####################
# def delete_campaign(campaign_id):
#     conn = get_db_connection()
#     sql = text(f"DELETE FROM {DIM_CAMPANHA_TABLE} WHERE id = :id")
#     try:
#         result = conn.execute(sql, {"id": campaign_id})
#         conn.commit()
#         return result.rowcount, None
#     except SQLAlchemyError as e:
#         conn.rollback()
#         return 0, str(e)
    
#####################
# DELETE SOFT
#####################
def delete_campaign(campaign_id):
    conn = get_db_connection()
    sql = text(f"UPDATE {DIM_CAMPANHA_TABLE} SET status = 0 WHERE id = :id")
    try:
        result = conn.execute(sql, {"id": campaign_id})
        conn.commit()
        return result.rowcount, None
    except SQLAlchemyError as e:
        conn.rollback()
        return 0, str(e)