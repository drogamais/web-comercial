# CORREÇÃO EM: drogamais/web-comercial/web-comercial-52b1f30afe463afa8ea727b0006a204b245c30d4/database/campanha_db.py

# database/campanha_db.py

from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError
from database.common_db import get_db_connection
import datetime

DIM_CAMPANHA_TABLE = "dim_campanha"
# Adicionado para fazer o JOIN
DIM_PARCEIRO_TABLE = "bronze_parceiros" 

def create_tables():
    conn = get_db_connection()
    if conn is None: return
    
    # --- PASSO 1: Criar a tabela se não existir (com a nova coluna) ---
    try:
        sql_create = text(f"""
            CREATE TABLE IF NOT EXISTS {DIM_CAMPANHA_TABLE} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                data_inicio DATE NOT NULL,
                data_fim DATE NOT NULL,
                status INT DEFAULT 1,
                parceiro_id INT DEFAULT NULL, 
                data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE(nome),
                FOREIGN KEY (parceiro_id) REFERENCES {DIM_PARCEIRO_TABLE}(id) ON DELETE SET NULL
            )
        """)
        conn.execute(sql_create)
        conn.commit()
    except SQLAlchemyError as e_create:
        # Se a criação falhar (ex: tabela existe mas sem FK), tentamos alterar
        print(f"Aviso ao criar tabela {DIM_CAMPANHA_TABLE}: {e_create}")
        conn.rollback()

    # --- PASSO 2: Garantir que a coluna `parceiro_id` exista (para tabelas antigas) ---
    # (Esta é a correção principal: é executada fora do 'except' anterior)
    try:
        sql_alter_col = text(f"""
            ALTER TABLE {DIM_CAMPANHA_TABLE}
            ADD COLUMN IF NOT EXISTS parceiro_id INT DEFAULT NULL
        """)
        conn.execute(sql_alter_col)
        conn.commit()
    except SQLAlchemyError as e_alter_col:
        # Ignora erros comuns de alteração (ex: coluna duplicada)
        if "Duplicate column name" in str(e_alter_col):
            pass # Coluna já existe, tudo bem
        else:
            print(f"Erro ao adicionar coluna parceiro_id: {e_alter_col}")
        conn.rollback()

    # --- PASSO 3: Garantir que a Foreign Key exista (para tabelas antigas) ---
    try:
        # Verifica se a FK já existe
        res = conn.execute(text(f"""
            SELECT COUNT(*)
            FROM information_schema.TABLE_CONSTRAINTS
            WHERE CONSTRAINT_SCHEMA = DATABASE()
              AND TABLE_NAME = '{DIM_CAMPANHA_TABLE}'
              AND CONSTRAINT_NAME = 'fk_campanha_parceiro'
        """))
        fk_exists = res.scalar() > 0

        if not fk_exists:
            sql_alter_fk = text(f"""
                ALTER TABLE {DIM_CAMPANHA_TABLE}
                ADD CONSTRAINT fk_campanha_parceiro
                FOREIGN KEY (parceiro_id) REFERENCES {DIM_PARCEIRO_TABLE}(id)
                ON DELETE SET NULL
            """)
            conn.execute(sql_alter_fk)
            conn.commit()
            
    except SQLAlchemyError as e_alter_fk:
        # Ignora erros de "FK já existe"
        if "Duplicate" in str(e_alter_fk) or "already exists" in str(e_alter_fk):
            pass
        else:
            print(f"Erro ao adicionar FK parceiro_id: {e_alter_fk}")
        conn.rollback()


def add_campaign(nome, data_inicio, data_fim, parceiro_id):
    conn = get_db_connection()
    sql = text(f"""
        INSERT INTO {DIM_CAMPANHA_TABLE} (nome, data_inicio, data_fim, status, parceiro_id) 
        VALUES (:nome, :data_inicio, :data_fim, 1, :parceiro_id)
    """)
    try:
        params = {
            "nome": nome, 
            "data_inicio": data_inicio, 
            "data_fim": data_fim,
            "parceiro_id": parceiro_id
        }
        conn.execute(sql, params)
        conn.commit()
        return None
    except SQLAlchemyError as e:
        conn.rollback()
        return str(e)

def get_all_campaigns():
    conn = get_db_connection()
    # Esta consulta agora deve funcionar, pois a coluna será criada no PASSO 2
    sql = text(f"""
        SELECT 
            c.*, 
            p.nome as parceiro_nome 
        FROM {DIM_CAMPANHA_TABLE} c
        LEFT JOIN {DIM_PARCEIRO_TABLE} p ON c.parceiro_id = p.id
        WHERE c.status = 1 
        ORDER BY c.data_inicio DESC
    """)
    try:
        cursor = conn.execute(sql)
        results = cursor.mappings().fetchall()
        cursor.close()
        return results
    except SQLAlchemyError as e:
        print(f"Erro ao buscar campanhas com parceiros: {e}")
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
    # Esta consulta também deve funcionar
    sql = text(f"""
        SELECT 
            c.*, 
            p.nome as parceiro_nome 
        FROM {DIM_CAMPANHA_TABLE} c
        LEFT JOIN {DIM_PARCEIRO_TABLE} p ON c.parceiro_id = p.id
        WHERE c.id = :id
    """)
    try:
        cursor = conn.execute(sql, {"id": campanha_id})
        result = cursor.mappings().fetchone()
        cursor.close()
        return result
    except SQLAlchemyError as e:
        print(f"Erro ao buscar campanha por id: {e}")
        return None

def update_campaign(campaign_id, nome, data_inicio, data_fim, parceiro_id):
    conn = get_db_connection()
    sql = text(f"""
        UPDATE {DIM_CAMPANHA_TABLE} SET 
            nome = :nome, 
            data_inicio = :data_inicio, 
            data_fim = :data_fim,
            parceiro_id = :parceiro_id
        WHERE id = :id
    """)
    try:
        params = {
            "nome": nome, 
            "data_inicio": data_inicio, 
            "data_fim": data_fim, 
            "parceiro_id": parceiro_id, 
            "id": campaign_id
        }
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