import os
from flask import Flask, render_template
from config import SECRET_KEY

# Importa os módulos de banco de dados
import database.campanha_db as database_campanha
import database.tabloide_db as database_tabloide
import database.parceiro_db as database_parceiros

# Importa os blueprints (nossos arquivos de rotas)
from routes.campanha_routes import campanha_bp
from routes.tabloide_routes import tabloide_bp
from routes.parceiro_routes import parceiro_bp

# Cria a aplicação Flask
app = Flask(__name__)

# Configurações principais
app.secret_key = SECRET_KEY
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Registra os blueprints (módulos) na aplicação principal
app.register_blueprint(campanha_bp)
app.register_blueprint(tabloide_bp)
app.register_blueprint(parceiro_bp) # NOVO


# --- Rota Principal (Home Page) ---
@app.route('/')
def index():
    """Renderiza a nova página inicial com os dois botões."""
    return render_template('index.html')

# --- Funções de Banco de Dados Globais ---
@app.before_request
def before_first_request():
    # Garante que as tabelas de todos os módulos sejam criadas
    database_campanha.create_tables()
    database_tabloide.create_tables()
    database_parceiros.create_tables() # NOVO

@app.teardown_appcontext
def teardown_db(exception):
    # Fecha todas as conexões de banco de dados
    database_campanha.close_db_connection(exception)
    database_tabloide.close_db_connection(exception)
    database_parceiros.close_db_connection(exception)
    database_campanha.close_drogamais_db_connection(exception)

if __name__ == '__main__':
    # Isso permite rodar 'python app.py' diretamente para testes
    app.run(host='0.0.0.0', port=5001, debug=True)