# database/common_db.py

import sqlalchemy
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError
from flask import g
from config import DB_CONFIG # Você ainda usa o config
from urllib.parse import quote_plus

# 1. Construir a URL de conexão para SQLAlchemy
# Formato: "mariadb+mariadb://<user>:<password>@<host>:<port>/<database>"
try:
    # 2. LÊ E ESCAPA A SENHA (e usuário, por segurança)
    # Isso converte caracteres especiais (como @) em formato de URL (como %40)
    safe_user = quote_plus(DB_CONFIG['user'])
    safe_password = quote_plus(DB_CONFIG['password'])
    
    DB_URL = (
        f"mysql+pymysql://{safe_user}:{safe_password}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG.get('port', 3306)}/{DB_CONFIG['database']}"
        f"?charset=utf8mb4"
    )
except KeyError:
    raise RuntimeError("DB_CONFIG em config.py está incompleto (faltando user, password, host ou database)")

# 2. Criar o Engine (o objeto que gerencia o pool)
try:
    engine = sqlalchemy.create_engine(
        DB_URL,
        pool_size=2,          # <-- SUA SUGESTÃO: Perfeito para Waitress!
        max_overflow=2,       # Conexões temporárias se o pool estiver cheio
        pool_recycle=3600,    # Recicla conexões após 1 hora (opcional, mas bom)
        pool_pre_ping=True    # <-- A SOLUÇÃO: Testa a conexão antes de usar
    )
except Exception as e:
    print(f"Erro ao criar o engine do SQLAlchemy: {e}")
    print(DB_URL)
    engine = None

# --- FUNÇÃO PARA OBTER CONEXÃO ---
def get_db_connection():
    """Obtém uma conexão do pool do SQLAlchemy."""
    try:
        if 'db_conn' not in g:
            if engine is None:
                 raise Exception("Engine do SQLAlchemy não está disponível.")
            g.db_conn = engine.connect()
        return g.db_conn
    except Exception as e:
        print(f"Erro ao obter conexão do pool SQLAlchemy: {e}")
        return None

# --- FUNÇÃO PARA FECHAR/DEVOLVER CONEXÃO ---
def close_db_connection(e=None):
    """Devolve a conexão ao pool do SQLAlchemy."""
    db = g.pop('db_conn', None)
    if db is not None:
        db.close() # No SQLAlchemy, .close() DEVOLVE a conexão ao pool

# --- FUNÇÕES DE BANCO (Refatoradas para SQLAlchemy) ---

def validate_gtins_in_external_db(gtin_list):
    if not gtin_list:
        return set(), None

    conn = get_db_connection()
    if conn is None:
        return None, "Não foi possível conectar ao banco de dados."

    try:
        # Cria placeholders seguros: :gtin_0, :gtin_1 ...
        placeholders = [f":gtin_{i}" for i in range(len(gtin_list))]
        sql_text = text(f"""
            SELECT codigo_barras_normalizado AS gtin
            FROM bronze_plugpharma_produtos
            WHERE `codigo_barras_normalizado` IN ({",".join(placeholders)})
        """)
        
        # Cria o dicionário de parâmetros: {'gtin_0': '123', 'gtin_1': '456'}
        params = {f"gtin_{i}": gtin for i, gtin in enumerate(gtin_list)}
        
        cursor = conn.execute(sql_text, params)
        validos = {row[0] for row in cursor.fetchall()}
        cursor.close()
        return validos, None
        
    except SQLAlchemyError as e:
        return None, str(e)


def get_codigo_interno_map_from_gtins(gtin_list):
    if not gtin_list:
        return {}, None

    conn = get_db_connection()
    if conn is None:
        return None, "Não foi possível conectar ao banco de dados."

    try:
        placeholders = [f":gtin_{i}" for i in range(len(gtin_list))]
        sql_text = text(f"""
            SELECT codigo_barras_normalizado, codigo_interno
            FROM bronze_plugpharma_produtos
            WHERE `codigo_barras_normalizado` IN ({",".join(placeholders)})
        """)
        
        params = {f"gtin_{i}": gtin for i, gtin in enumerate(gtin_list)}
        
        cursor = conn.execute(sql_text, params)
        # .mappings() permite acessar por nome da coluna, como dictionary=True
        validos_map = {row['codigo_barras_normalizado']: row['codigo_interno'] for row in cursor.mappings().fetchall()}
        cursor.close()
        return validos_map, None
        
    except SQLAlchemyError as e:
        return None, str(e)