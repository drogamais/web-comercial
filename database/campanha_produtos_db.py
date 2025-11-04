# database/campanha_produtos_db.py

from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError
from database.common_db import get_db_connection

DIM_CAMPANHA_TABLE = "dim_campanha"
DIM_CAMPANHA_PRODUTO_TABLE = "dim_campanha_produto"

def create_product_table():
    conn = get_db_connection()
    if conn is None: return
    try:
        sql_create_fact = text(f"""
            CREATE TABLE IF NOT EXISTS {DIM_CAMPANHA_PRODUTO_TABLE} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                campanha_id INT NOT NULL,
                codigo_barras VARCHAR(14),
                codigo_barras_normalizado VARCHAR(14) DEFAULT NULL,
                codigo_interno VARCHAR(14) DEFAULT NULL,
                descricao TEXT,
                pontuacao INT,
                preco_normal DECIMAL(10, 2),
                preco_desconto DECIMAL(10, 2),
                rebaixe DECIMAL(10, 2),
                qtd_limite INT,
                data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (campanha_id) REFERENCES {DIM_CAMPANHA_TABLE}(id) ON DELETE CASCADE
            )
        """)
        conn.execute(sql_create_fact)
        
        sql_alter = text(f"""
            ALTER TABLE {DIM_CAMPANHA_PRODUTO_TABLE}
            ADD COLUMN IF NOT EXISTS codigo_barras_normalizado VARCHAR(14) DEFAULT NULL
            AFTER codigo_barras;
        """)
        conn.execute(sql_alter)
        conn.commit()
    except SQLAlchemyError as e:
        print(f"Erro ao criar/alterar tabela {DIM_CAMPANHA_PRODUTO_TABLE}: {e}")
        conn.rollback()


def add_products_bulk(produtos):
    conn = get_db_connection()
    sql = text(f"""
        INSERT INTO {DIM_CAMPANHA_PRODUTO_TABLE} (
            campanha_id, codigo_barras, codigo_barras_normalizado, codigo_interno, descricao, pontuacao,
            preco_normal, preco_desconto, rebaixe, qtd_limite
        )
        VALUES (:cid, :cb, :cbn, :ci, :desc, :pts, :pr_norm, :pr_desc, :reb, :qtd)
    """)
    
    try:
        # Mapeia a lista de tuplas para uma lista de dicionários
        produtos_dict = [
            {
                "cid": p[0], "cb": p[1], "cbn": p[2], "ci": p[3], "desc": p[4],
                "pts": p[5], "pr_norm": p[6], "pr_desc": p[7], "reb": p[8], "qtd": p[9]
            }
            for p in produtos
        ]
        
        result = conn.execute(sql, produtos_dict)
        conn.commit()
        return result.rowcount, None
    except SQLAlchemyError as e:
        conn.rollback()
        return 0, str(e)

def get_products_by_campaign_id(campanha_id):
    conn = get_db_connection()
    sql = text(f"SELECT * FROM {DIM_CAMPANHA_PRODUTO_TABLE} WHERE campanha_id = :id")
    try:
        cursor = conn.execute(sql, {"id": campanha_id})
        results = cursor.mappings().fetchall()
        cursor.close()
        return results
    except SQLAlchemyError as e:
        print(f"Erro em get_products_by_campaign_id: {e}")
        return []

def add_single_product(dados_produto):
    conn = get_db_connection()
    sql = text(f"""
        INSERT INTO {DIM_CAMPANHA_PRODUTO_TABLE} (
            campanha_id, codigo_barras, codigo_barras_normalizado, codigo_interno, descricao, pontuacao,
            preco_normal, preco_desconto, rebaixe, qtd_limite
        )
        VALUES (:cid, :cb, :cbn, :ci, :desc, :pts, :pr_norm, :pr_desc, :reb, :qtd)
    """)
    try:
        params = {
            "cid": dados_produto[0], "cb": dados_produto[1], "cbn": dados_produto[2], 
            "ci": dados_produto[3], "desc": dados_produto[4], "pts": dados_produto[5],
            "pr_norm": dados_produto[6], "pr_desc": dados_produto[7], "reb": dados_produto[8], 
            "qtd": dados_produto[9]
        }
        result = conn.execute(sql, params)
        conn.commit()
        return result.rowcount, None
    except SQLAlchemyError as e:
        conn.rollback()
        return 0, str(e)

def update_products_in_bulk(produtos_para_atualizar):
    conn = get_db_connection()
    sql = text(f"""
        UPDATE {DIM_CAMPANHA_PRODUTO_TABLE} SET
            codigo_barras = :cb, codigo_barras_normalizado = :cbn, codigo_interno = :ci, 
            descricao = :desc, pontuacao = :pts, preco_normal = :pr_norm, 
            preco_desconto = :pr_desc, rebaixe = :reb, qtd_limite = :qtd
        WHERE id = :id
    """)
    try:
        # Mapeia a lista de tuplas para uma lista de dicionários
        produtos_dict = [
            {
                "cb": p[0], "cbn": p[1], "ci": p[2], "desc": p[3], "pts": p[4],
                "pr_norm": p[5], "pr_desc": p[6], "reb": p[7], "qtd": p[8], "id": p[9]
            }
            for p in produtos_para_atualizar
        ]
        
        result = conn.execute(sql, produtos_dict)
        conn.commit()
        return result.rowcount, None
    except SQLAlchemyError as e:
        conn.rollback()
        return 0, str(e)

def delete_products_in_bulk(ids_para_deletar):
    conn = get_db_connection()
    if not ids_para_deletar:
        return 0, None
    
    try:
        # Cria placeholders seguros: :id_0, :id_1 ...
        placeholders = [f":id_{i}" for i in range(len(ids_para_deletar))]
        sql_text = text(f"""
            DELETE FROM {DIM_CAMPANHA_PRODUTO_TABLE} 
            WHERE id IN ({",".join(placeholders)})
        """)
        
        # Cria o dicionário de parâmetros: {'id_0': '1', 'id_1': '2'}
        params = {f"id_{i}": id_val for i, id_val in enumerate(ids_para_deletar)}
        
        result = conn.execute(sql_text, params)
        conn.commit()
        return result.rowcount, None
    except SQLAlchemyError as e:
        conn.rollback()
        return 0, str(e)

def delete_products_by_campaign_id(campanha_id):
    conn = get_db_connection()
    sql = text(f"DELETE FROM {DIM_CAMPANHA_PRODUTO_TABLE} WHERE campanha_id = :cid")
    try:
        result = conn.execute(sql, {"cid": campanha_id})
        conn.commit()
        return result.rowcount, None
    except SQLAlchemyError as e:
        conn.rollback()
        return 0, str(e)
    
def update_product_ci_bulk(produtos_para_atualizar):
    """
    Atualiza GBC, GBC_Normalizado e Codigo_Interno em massa.
    Espera uma lista de tuplas: (cb, cbn, ci, id)
    """
    conn = get_db_connection()
    if not produtos_para_atualizar:
        return 0, None
    
    sql = text(f"""
        UPDATE {DIM_CAMPANHA_PRODUTO_TABLE} SET
            codigo_barras = :cb, 
            codigo_barras_normalizado = :cbn, 
            codigo_interno = :ci
        WHERE id = :id
    """)
    try:
        produtos_dict = [
            {"cb": p[0], "cbn": p[1], "ci": p[2], "id": p[3]}
            for p in produtos_para_atualizar
        ]
        result = conn.execute(sql, produtos_dict)
        conn.commit()
        return result.rowcount, None
    except SQLAlchemyError as e:
        conn.rollback()
        return 0, str(e)