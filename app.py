# app.py

import os
from flask import Flask, render_template
from config import SECRET_KEY

# Importa os módulos de banco de dados
import database.common_db as database_common # <<< PRECISA DESTE
import database.campanha_db as database_campanha
import database.tabloide_db as database_tabloide
import database.parceiro_db as database_parceiros
import database.campanha_produtos_db as database_campanha_produtos
import database.tabloide_produtos_db as database_tabloide_produtos

# Importa os blueprints (nossos arquivos de rotas)
from routes.campanha_routes import campanha_bp
from routes.tabloide_routes import tabloide_bp
from routes.parceiro_routes import parceiro_bp
from routes.campanha_produtos_routes import campanha_produtos_bp
from routes.tabloide_produtos_routes import tabloide_produtos_bp


# Cria a aplicação Flask
app = Flask(__name__)

# Configurações principais
app.secret_key = SECRET_KEY
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Registra os blueprints (módulos) na aplicação principal
app.register_blueprint(campanha_bp)
app.register_blueprint(tabloide_bp)
app.register_blueprint(parceiro_bp)
# --- REGISTRO DOS NOVOS BLUEPRINTS ---
app.register_blueprint(campanha_produtos_bp)
app.register_blueprint(tabloide_produtos_bp)


# --- Rota Principal (Home Page) ---
@app.route('/')
def index():
    """Renderiza a nova página inicial com os botões."""
    # Busca parceiros que vencem em 30 dias
    expiring_partners = database_parceiros.get_expiring_parceiros(days_ahead=30) 
    
    return render_template(
        'index.html', 
        active_page='index',
        expiring_partners=expiring_partners # <-- ADICIONADO
    )

# --- Funções de Banco de Dados Globais ---
# A função before_request permanece a mesma, pois ainda precisa chamar
# as funções de criação de tabela de cada módulo.
@app.before_request
def before_first_request():
    database_campanha.create_tables() #
    database_tabloide.create_tables() #
    database_parceiros.create_tables() #
    database_campanha_produtos.create_product_table() #
    database_tabloide_produtos.create_product_table() #

# --- MODIFICADO AQUI ---
@app.teardown_appcontext
def teardown_db(exception):
    database_common.close_db_connection(exception) 

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)