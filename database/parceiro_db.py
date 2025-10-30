from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError
from database.common_db import get_db_connection

DIM_PARCEIRO_TABLE = "bronze_parceiros"


def create_tables():
    conn = get_db_connection()
    if conn is None:
        return
    try:
        # Tabela FINAL com os campos DEFINITIVOS (incluindo o UNIQUE INDEX)
        sql_create = text(f"""
            CREATE TABLE IF NOT EXISTS {DIM_PARCEIRO_TABLE} (
                id INT AUTO_INCREMENT PRIMARY KEY,
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
                data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP 
                    ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE INDEX unique_parceiro_nome_data (nome_ajustado, data_entrada, data_saida)
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


def get_all_parceiros():
    conn = get_db_connection()
    sql = text(f"SELECT * FROM {DIM_PARCEIRO_TABLE} ORDER BY nome_ajustado ASC")
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


def update_parceiro(parceiro_id, **data):
    """
    Atualiza um parceiro existente.
    Usa **data para atualizar qualquer campo dinamicamente.
    """
    conn = get_db_connection()

    # Gera automaticamente "coluna = :coluna" para cada campo
    set_clause = ", ".join([f"{key} = :{key}" for key in data.keys()])
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