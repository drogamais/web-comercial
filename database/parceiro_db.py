# database/parceiro_db.py

from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError
from database.common_db import get_db_connection

DIM_PARCEIRO_TABLE = "bronze_parceiros"


def create_tables():
    conn = get_db_connection()
    if conn is None:
        return
    try:
        sql_create = text(f"""
            CREATE TABLE IF NOT EXISTS {DIM_PARCEIRO_TABLE} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                api_user_id VARCHAR(50) DEFAULT NULL, 
                nome_ajustado VARCHAR(255) NOT NULL,
                tipo VARCHAR(100) DEFAULT NULL,
                cnpj VARCHAR(20) DEFAULT NULL,
                nome_fantasia VARCHAR(255) DEFAULT NULL,
                razao_social VARCHAR(255) DEFAULT NULL,
                gestor VARCHAR(255) DEFAULT NULL,
                telefone_gestor VARCHAR(20) DEFAULT NULL,
                email_gestor VARCHAR(255) DEFAULT NULL,
                data_entrada DATE DEFAULT NULL,
                data_saida DATE DEFAULT NULL,
                status TINYINT DEFAULT 1,
                `senha_definida` TINYINT(1) NOT NULL DEFAULT '0',
                data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP 
                    ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_api_user_id (api_user_id) 
            )
        """)
        conn.execute(sql_create)

        conn.commit()
    except SQLAlchemyError as e:
        print(f"Erro ao criar tabela base {DIM_PARCEIRO_TABLE}: {e}")
        conn.rollback()


def add_parceiro(**data):
    """
    Insere um novo parceiro.
    Espera receber todos os campos via dicionário (ex: add_parceiro(**data))
    """
    conn = get_db_connection()

    # Gera automaticamente a lista de colunas e placeholders
    # Garante que 'api_user_id' esteja incluído se existir em 'data'
    columns = ", ".join(data.keys())
    placeholders = ", ".join([f":{key}" for key in data.keys()])

    sql = text(f"""
        INSERT INTO {DIM_PARCEIRO_TABLE} ({columns})
        VALUES ({placeholders})
    """)

    try:
        conn.execute(sql, data)
        conn.commit()
        return None
    except SQLAlchemyError as e:
        conn.rollback()
        return str(e)


def get_all_parceiros(tipo=None, status=None, data_entrada_min=None, data_saida_max=None):
    conn = get_db_connection()
    sql_base = f"SELECT * FROM {DIM_PARCEIRO_TABLE}"
    where_clauses = []
    params = {}
    
    # 1. Filtro por Tipo
    if tipo and tipo.upper() in ["INDUSTRIA", "DISTRIBUIDOR"]:
        where_clauses.append("tipo = :tipo")
        params["tipo"] = tipo
        
    # 2. Filtro por Status
    if status is None or status == '1': 
        where_clauses.append("status = 1") 
    elif status == '0': 
        where_clauses.append("status = 0")
        
    # 3. Filtro por Data Entrada
    if data_entrada_min:
        where_clauses.append("data_entrada >= :data_entrada_min")
        params["data_entrada_min"] = data_entrada_min
        
    # 4. Filtro por Data Saída
    if data_saida_max:
        where_clauses.append("data_saida <= :data_saida_max")
        params["data_saida_max"] = data_saida_max
    
    where_str = ""
    if where_clauses:
        where_str = " WHERE " + " AND ".join(where_clauses)
    
    sql = text(f"{sql_base} {where_str} ORDER BY nome_ajustado ASC")
    
    try:
        cursor = conn.execute(sql, params)
        results = cursor.mappings().fetchall()
        cursor.close()
        return results
    except SQLAlchemyError as e:
        print(f"Erro ao buscar parceiros: {e}")
        return []


def get_parceiro_by_id(parceiro_id):
    conn = get_db_connection()
    # Busca pelo ID local (auto-increment)
    sql = text(f"SELECT * FROM {DIM_PARCEIRO_TABLE} WHERE id = :id")
    try:
        cursor = conn.execute(sql, {"id": parceiro_id})
        result = cursor.mappings().fetchone()
        cursor.close()
        return result
    except SQLAlchemyError as e:
        print(f"Erro ao buscar parceiro por id: {e}")
        return None


def update_parceiro(parceiro_id, **data):
    """
    Atualiza um parceiro existente.
    """
    conn = get_db_connection()

    # Remove 'api_user_id' dos dados de atualização,
    # pois não queremos atualizar essa chave, apenas usá-la.
    # (Embora aqui estejamos atualizando pelo 'id' local)
    data.pop('api_user_id', None) 

    set_clause = ", ". join([f"{key} = :{key}" for key in data.keys()])
    sql = text(f"""
        UPDATE {DIM_PARCEIRO_TABLE}
        SET {set_clause}
        WHERE id = :id
    """)

    try:
        data["id"] = parceiro_id
        result = conn.execute(sql, data)
        conn.commit()
        return result.rowcount, None
    except SQLAlchemyError as e:
        conn.rollback()
        return 0, str(e)
    
def set_senha_definida_flag(parceiro_id):
    """Marca a flag 'senha_definida' como 1 (true) para um parceiro."""
    conn = get_db_connection()
    if conn is None:
        return "Falha na conexão com o banco"

    sql = text(f"UPDATE {DIM_PARCEIRO_TABLE} SET senha_definida = 1 WHERE id = :id")
    try:
        conn.execute(sql, {"id": parceiro_id})
        conn.commit()
        return None
    except SQLAlchemyError as e:
        conn.rollback()
        return str(e)


def delete_parceiro(parceiro_id):
    conn = get_db_connection()
    sql = text(f"DELETE FROM {DIM_PARCEIRO_TABLE} WHERE id = :id")
    try:
        result = conn.execute(sql, {"id": parceiro_id})
        conn.commit()
        return result.rowcount, None
    except SQLAlchemyError as e:
        conn.rollback()
        return 0, str(e)
    
