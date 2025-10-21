# aplicacao_web_campanhas/database_campanha.py

import mysql.connector
from mysql.connector import Error
from flask import g
from config import DB_CONFIG
import datetime # Adicionado para comparar datas

def get_db_connection():
    try:
        if 'db' not in g:
            g.db = mysql.connector.connect(**DB_CONFIG)
        return g.db
    except Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
        return None

def close_db_connection(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def create_tables():
    conn = get_db_connection()
    if conn is None: return
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campanhas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                data_inicio DATE NOT NULL,
                data_fim DATE NOT NULL,
                status INT DEFAULT 1,  -- 1 = Ativo, 0 = Inativo (Soft Delete)
                UNIQUE(nome)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                campanha_id INT NOT NULL,
                codigo_barras VARCHAR(50),
                descricao VARCHAR(255),
                pontuacao INT,
                preco_normal DECIMAL(10, 2),
                preco_desconto DECIMAL(10, 2),
                rebaixe DECIMAL(10, 2),
                qtd_limite INT,
                FOREIGN KEY (campanha_id) REFERENCES campanhas(id) ON DELETE CASCADE
            )
        """)
        conn.commit()
    except Error as e:
        print(f"Erro ao criar tabelas: {e}")
    finally:
        cursor.close()

def add_campaign(nome, data_inicio, data_fim):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Garante que novas campanhas sejam criadas como ativas (status=1)
        cursor.execute("INSERT INTO campanhas (nome, data_inicio, data_fim, status) VALUES (%s, %s, %s, 1)",
                       (nome, data_inicio, data_fim))
        conn.commit()
        return None
    except Error as e:
        conn.rollback()
        return str(e)
    finally:
        cursor.close()

def get_all_campaigns():
    """Busca todas as campanhas ATIVAS (status=1)."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # Modificado para buscar apenas campanhas com status = 1
    cursor.execute("SELECT * FROM campanhas WHERE status = 1 ORDER BY data_inicio DESC")
    return cursor.fetchall()

def get_active_campaigns_for_upload():
    """
    Busca campanhas ativas (status=1) e que ainda não expiraram (data_fim >= hoje).
    Usado na página de Upload.
    """
    conn = get_db_connection()
    if conn is None: return []
    cursor = conn.cursor(dictionary=True)
    today = datetime.date.today()
    try:
        cursor.execute(
            "SELECT * FROM campanhas WHERE status = 1 AND data_fim >= %s ORDER BY data_inicio DESC",
            (today,)
        )
        return cursor.fetchall()
    except Error as e:
        print(f"Erro ao buscar campanhas ativas para upload: {e}")
        return []
    finally:
        cursor.close()


def get_campaign_by_id(campanha_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # Busca mesmo se estiver inativa, para permitir visualização de produtos antigos
    cursor.execute("SELECT * FROM campanhas WHERE id = %s", (campanha_id,))
    return cursor.fetchone()

def update_campaign(campaign_id, nome, data_inicio, data_fim):
    """Atualiza os dados de uma campanha existente."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """
        UPDATE campanhas SET nome = %s, data_inicio = %s, data_fim = %s
        WHERE id = %s
    """
    try:
        cursor.execute(sql, (nome, data_inicio, data_fim, campaign_id))
        conn.commit()
        return cursor.rowcount, None
    except Error as e:
        conn.rollback()
        return 0, str(e)
    finally:
        cursor.close()

def delete_campaign(campaign_id):
    """Realiza um soft delete de uma campanha (define status = 0)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Alterado de DELETE para UPDATE (Soft Delete)
    sql = "UPDATE campanhas SET status = 0 WHERE id = %s"
    try:
        cursor.execute(sql, (campaign_id,))
        conn.commit()
        return cursor.rowcount, None
    except Error as e:
        conn.rollback()
        return 0, str(e)
    finally:
        cursor.close()

def add_products_bulk(produtos):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """
        INSERT INTO produtos (campanha_id, codigo_barras, descricao, pontuacao, preco_normal, preco_desconto, rebaixe, qtd_limite)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        cursor.executemany(sql, produtos)
        conn.commit()
        return cursor.rowcount, None
    except Error as e:
        conn.rollback()
        return 0, str(e)
    finally:
        cursor.close()

def get_products_by_campaign_id(campanha_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM produtos WHERE campanha_id = %s", (campanha_id,))
    return cursor.fetchall()

def add_single_product(dados_produto):
    """Adiciona um único produto ao banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """
        INSERT INTO produtos (campanha_id, codigo_barras, descricao, pontuacao, preco_normal, preco_desconto, rebaixe, qtd_limite)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        cursor.execute(sql, dados_produto)
        conn.commit()
        return cursor.rowcount, None
    except Error as e:
        conn.rollback()
        return 0, str(e)
    finally:
        cursor.close()

def update_products_in_bulk(produtos_para_atualizar):
    """Atualiza múltiplos produtos no banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """
        UPDATE produtos SET
            codigo_barras = %s, descricao = %s, pontuacao = %s,
            preco_normal = %s, preco_desconto = %s, rebaixe = %s, qtd_limite = %s
        WHERE id = %s
    """
    try:
        cursor.executemany(sql, produtos_para_atualizar)
        conn.commit()
        return cursor.rowcount, None
    except Error as e:
        conn.rollback()
        return 0, str(e)
    finally:
        cursor.close()

def delete_products_in_bulk(ids_para_deletar):
    """Deleta múltiplos produtos do banco de dados com base em seus IDs."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Prepara a query para aceitar uma lista de IDs
    format_strings = ','.join(['%s'] * len(ids_para_deletar))
    sql = f"DELETE FROM produtos WHERE id IN ({format_strings})"
    try:
        cursor.execute(sql, tuple(ids_para_deletar))
        conn.commit()
        return cursor.rowcount, None
    except Error as e:
        conn.rollback()
        return 0, str(e)
    finally:
        cursor.close()

# --- NOVAS FUNÇÕES PARA VALIDAR GTIN NO dbDrogamais ---

def get_drogamais_db_connection():
    """
    Cria uma nova conexão de banco de dados especificamente para o dbDrogamais.
    (VERSÃO CORRIGIDA - Não herda 'collation')
    """
    try:
        config_drogamais = {
            "user": DB_CONFIG.get("user"),
            "password": DB_CONFIG.get("password"),
            "host": DB_CONFIG.get("host"),
            "port": DB_CONFIG.get("port", 3306), # Usa 3306 como padrão
            "database": "dbDrogamais", # Define o banco de dados
            "collation": "utf8mb4_general_ci"
        }

        if 'db_drogamais' not in g:
            # Conecta usando a configuração limpa
            g.db_drogamais = mysql.connector.connect(**config_drogamais)
        return g.db_drogamais
        
    except Error as e:
        print(f"Erro ao conectar ao dbDrogamais: {e}")
        return None

def close_drogamais_db_connection(e=None):
    """ Fecha a conexão específica do dbDrogamais """
    db = g.pop('db_drogamais', None)
    if db is not None:
        db.close()

def validate_gtins_in_external_db(gtin_list):
    """
    Verifica uma lista de GTINs contra as tabelas bronze (vendas e estoque) no dbDrogamais.
    Retorna um SET contendo apenas os GTINs que FORAM ENCONTRADOS (válidos).
    
    (Query ATUALIZADA para usar bronze_plugpharma_vendas e bronze_plugpharma_estoque)
    """
    if not gtin_list:
        return set(), None

    conn = get_drogamais_db_connection()
    if conn is None:
        return None, "Não foi possível conectar ao banco de dados dbDrogamais."

    cursor = conn.cursor()
    try:
        # Cria placeholders (%s) para a lista de GTINs
        format_strings = ','.join(['%s'] * len(gtin_list))
        
        # SQL CORRIGIDO:
        # 1. Usa UNION para combinar os resultados das duas tabelas.
        # 2. Usa um alias (AS gtin) para que as colunas de nomes diferentes
        #    sejam tratadas como uma só no resultado.
        # 3. Adiciona backticks (`) em 'código_de_barras' por causa do acento.
        sql = f"""
            (
                SELECT codigo_de_barras_normalizado_produto AS gtin
                FROM bronze_plugpharma_vendas
                WHERE codigo_de_barras_normalizado_produto IN ({format_strings})
            )
            UNION
            (
                SELECT `código_de_barras` AS gtin
                FROM bronze_plugpharma_estoque
                WHERE `código_de_barras` IN ({format_strings})
            )
        """
        
        params = tuple(gtin_list) + tuple(gtin_list)        
        cursor.execute(sql, params)
        
        # Retorna um set (ex: {'789...', '789...'}) dos GTINs encontrados
        validos = {row[0] for row in cursor.fetchall()}
        return validos, None
        
    except Error as e:
        return None, str(e)
    finally:
        if cursor:
            cursor.close()