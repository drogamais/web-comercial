# database/tabloide_produtos_db.py

from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError
from database.common_db import get_db_connection

DIM_TABLOIDE_TABLE = "dim_tabloide"
DIM_TABLOIDE_PRODUTO_TABLE = "dim_tabloide_produto"

def create_product_table():
    conn = get_db_connection()
    if conn is None: return
    try:
        sql_create = text(f"""
            CREATE TABLE IF NOT EXISTS {DIM_TABLOIDE_PRODUTO_TABLE} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                tabloide_id INT NOT NULL,
                codigo_barras VARCHAR(14),
                codigo_barras_normalizado VARCHAR(14) DEFAULT NULL,
                codigo_interno VARCHAR(14) DEFAULT NULL,
                descricao TEXT,
                laboratorio VARCHAR(255),
                tipo_preco VARCHAR(100) DEFAULT NULL,
                preco_normal DECIMAL(10, 2),
                preco_desconto DECIMAL(10, 2),
                preco_desconto_cliente DECIMAL(10, 2),
                preco_app DECIMAL(10, 2),
                tipo_regra VARCHAR(100),
                data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (tabloide_id) REFERENCES {DIM_TABLOIDE_TABLE}(id) ON DELETE CASCADE
            )
        """)
        conn.execute(sql_create)
        
        sql_alter = text(f"""
            ALTER TABLE {DIM_TABLOIDE_PRODUTO_TABLE}
            ADD COLUMN IF NOT EXISTS codigo_barras_normalizado VARCHAR(14) DEFAULT NULL
            AFTER codigo_barras;
        """)
        conn.execute(sql_alter)
        conn.commit()
    except SQLAlchemyError as e:
        print(f"Erro ao criar/alterar tabela {DIM_TABLOIDE_PRODUTO_TABLE} (Tabloide): {e}")
        conn.rollback()

def add_products_bulk(produtos):
    conn = get_db_connection()
    sql = text(f"""
        INSERT INTO {DIM_TABLOIDE_PRODUTO_TABLE} (
            tabloide_id, codigo_barras, codigo_barras_normalizado, codigo_interno, descricao, laboratorio,
            tipo_preco, preco_normal, preco_desconto, preco_desconto_cliente, preco_app, tipo_regra
        )
        VALUES (:cid, :cb, :cbn, :ci, :desc, :lab, :tipo_pr, :pr_norm, :pr_desc, :pr_cli, :pr_app, :tipo_regra)
    """)
    try:
        produtos_dict = [
            {
                "cid": p[0], "cb": p[1], "cbn": p[2], "ci": p[3], "desc": p[4], "lab": p[5],
                "tipo_pr": p[6], "pr_norm": p[7], "pr_desc": p[8], "pr_cli": p[9], "pr_app": p[10], "tipo_regra": p[11]
            }
            for p in produtos
        ]
        result = conn.execute(sql, produtos_dict)
        conn.commit()
        return result.rowcount, None
    except SQLAlchemyError as e:
        conn.rollback()
        return 0, str(e)

def get_products_by_campaign_id(tabloide_id):
    conn = get_db_connection()
    sql = text(f"SELECT * FROM {DIM_TABLOIDE_PRODUTO_TABLE} WHERE tabloide_id = :id")
    try:
        cursor = conn.execute(sql, {"id": tabloide_id})
        results = cursor.mappings().fetchall()
        cursor.close()
        return results
    except SQLAlchemyError as e:
        print(f"Erro em get_products_by_tabloide_id (tabloide): {e}")
        return []

def add_single_product(dados_produto):
    conn = get_db_connection()
    sql = text(f"""
        INSERT INTO {DIM_TABLOIDE_PRODUTO_TABLE} (
            tabloide_id, codigo_barras, codigo_barras_normalizado, codigo_interno, descricao, laboratorio,
            tipo_preco, preco_normal, preco_desconto, preco_desconto_cliente, preco_app, tipo_regra
        )
        VALUES (:cid, :cb, :cbn, :ci, :desc, :lab, :tipo_pr, :pr_norm, :pr_desc, :pr_cli, :pr_app, :tipo_regra)
    """)
    try:
        params = {
            "cid": dados_produto[0], "cb": dados_produto[1], "cbn": dados_produto[2], 
            "ci": dados_produto[3], "desc": dados_produto[4], "lab": dados_produto[5],
            "tipo_pr": dados_produto[6], "pr_norm": dados_produto[7], "pr_desc": dados_produto[8], 
            "pr_cli": dados_produto[9], "pr_app": dados_produto[10], "tipo_regra": dados_produto[11]
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
        UPDATE {DIM_TABLOIDE_PRODUTO_TABLE} SET
            codigo_barras = :cb, codigo_barras_normalizado = :cbn, codigo_interno = :ci, 
            descricao = :desc, laboratorio = :lab, tipo_preco = :tipo_pr, 
            preco_normal = :pr_norm, preco_desconto = :pr_desc, 
            preco_desconto_cliente = :pr_cli, preco_app = :pr_app, tipo_regra = :tipo_regra
        WHERE id = :id
    """)
    try:
        produtos_dict = [
            {
                "cb": p[0], "cbn": p[1], "ci": p[2], "desc": p[3], "lab": p[4],
                "tipo_pr": p[5], "pr_norm": p[6], "pr_desc": p[7], "pr_cli": p[8],
                "pr_app": p[9], "tipo_regra": p[10], "id": p[11]
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
        placeholders = [f":id_{i}" for i in range(len(ids_para_deletar))]
        sql_text = text(f"""
            DELETE FROM {DIM_TABLOIDE_PRODUTO_TABLE} 
            WHERE id IN ({",".join(placeholders)})
        """)
        
        params = {f"id_{i}": id_val for i, id_val in enumerate(ids_para_deletar)}
        
        result = conn.execute(sql_text, params)
        conn.commit()
        return result.rowcount, None
    except SQLAlchemyError as e:
        conn.rollback()
        return 0, str(e)

def delete_products_by_tabloide_id(tabloide_id):
    conn = get_db_connection()
    sql = text(f"DELETE FROM {DIM_TABLOIDE_PRODUTO_TABLE} WHERE tabloide_id = :cid")
    try:
        result = conn.execute(sql, {"cid": tabloide_id})
        conn.commit()
        return result.rowcount, None
    except SQLAlchemyError as e:
        conn.rollback()
        return 0, str(e)