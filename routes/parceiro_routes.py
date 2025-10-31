from flask import Blueprint, render_template, request, redirect, url_for, flash
import database.parceiro_db as db
from utils import DELETE_PASSWORD
#from config import EMBEDDED_API_KEY
import requests 
import json     
from datetime import datetime
import time

# Campos principais do parceiro
PARCEIRO_FIELDS = (
    "nome_ajustado", "tipo", "cnpj", "nome_fantasia", "razao_social",
    "gestor", "telefone_gestor", "email_gestor"
)

parceiro_bp = Blueprint(
    'parceiro', __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/parceiro'
)

# --- URL da API POWEREMBEDDED ---

EMBEDDED_API_URL = "https://api.powerembedded.com.br/api/user"
EMBEDDED_API_KEY = "eyJPcmdJZCI6Ijc5MTVmZmU1LWE4MWUtNDA4Ni04MDNkLTQzM2M4OTJkZDc4NSIsIkFwaUtleSI6IkFBXzM2OVpvQlRNc04yczBwbjJpY2RHZC1PdlNrN2ZVTlJuaEo4NGdOMWcifQ"
# ----------------------------------------

def _get_form_data(form, sufixo=""):
    """Extrai e normaliza os dados do formulário."""
    data = {field: (form.get(f"{field}{sufixo}") or None) for field in PARCEIRO_FIELDS}
    data["data_entrada"] = form.get(f"data_entrada{sufixo}") or None
    data["data_saida"] = form.get(f"data_saida{sufixo}") or None
    data["status"] = 1
    return data

def _cadastrar_parceiro_embedded(data):

    try:
        expiration_date_iso = None
        if data.get("data_saida"):
            dt_end = datetime.strptime(data.get("data_saida"), '%Y-%m-%d')
            expiration_date_iso = dt_end.strftime('%Y-%m-%dT00:00:00Z')
    
    except ValueError as e:
        return False, f"Formato de data inválido. Use AAAA-MM-DD. Erro: {e}"
    # --- FIM DA FORMATAÇÃO ---

    # 1. Mapear os dados do Formulário para o Payload de 'api/user'
    #    Assumindo que 'email_gestor' é o 'email' do usuário
    #    e 'gestor' é o 'name' do usuário.
    user_email = data.get("email_gestor")
    user_name = data.get("nome_fantasia") # Usa Gestor, ou o Nome Ajustado

    if not user_email:
        return False, "O campo 'E-mail Gestor' é obrigatório para a API."

    if not user_name:
        return False, "O campo 'Gestor' ou 'Nome Ajustado' é obrigatório para a API."

    timestamp = int(time.time())
    email_de_teste = f"teste.script.{timestamp}@exemplo.com"

    payload = {
        "email": user_email,
        "name": user_name,
        "role": 1, # <<< USANDO O VALOR PADRÃO 1
        "department": data.get("tipo"), # Mapeando 'Tipo' (INDUSTRIA) para 'department'
        "expirationDate": expiration_date_iso, # Usa a data de saída
        
        # "email": email_de_teste, # Email agora é único
        # "name": f"Usuario Teste Script {timestamp}",
        # "role": 1,
        # "department": "INDUSTRIA",
        # "expirationDate": "2025-12-31T00:00:00Z",
        # "canExportReport": True,
        "reportLandingPage": None, 
        "windowsAdUser": None, 
        "bypassFirewall": False,
        "canEditReport": False, 
        "canCreateReport": False, 
        "canOverwriteReport": False,
        "canRefreshDataset": False, 
        "canCreateSubscription": False, 
        "canDownloadPbix": False,
        "canExportReportWithHiddenPages": False, 
        "canCreateNewUsers": False,
        "canStartCapacityByDemand": False, 
        "canDisplayVisualHeaders": True,
        "canExportReportOtherPages": False, 
        "accessReportAnyTime": True,
        "sendWelcomeEmail": True
    }

    # 2. Configure os Headers de autenticação (Bearer Token)
    headers = {
        "X-API-Key": EMBEDDED_API_KEY, # <-- CORRIGIDO
        "Content-Type": "application/json",
        "Accept": "application/json" # É bom adicionar este também
    }

    try:
        # 3. Faça a chamada POST para a API (agora em /api/user)
        response = requests.post(EMBEDDED_API_URL, headers=headers, json=payload, timeout=10)

        # 4. Verifique se a API respondeu com sucesso
        if response.status_code == 200: # Rota 'user' responde com 200 (OK)
            return True, None # Sucesso
        elif response.status_code == 401:
            return False, "API Erro 401: Não Autorizado. Verifique sua Chave de API (Token)."
        else:
            # A API retornou outro erro
            try:
                error_details = response.json().get("message", "Erro desconhecido")
            except json.JSONDecodeError:
                error_details = response.text
            
            return False, f"API Embedded Erro {response.status_code}: {error_details}"

    except requests.exceptions.RequestException as e:
        # Erro de conexão, timeout, etc.
        return False, f"Falha ao conectar na API Embedded: {e}"

@parceiro_bp.route('/gerenciar', methods=['GET', 'POST'])
def gestao_parceiros():
    if request.method == 'POST':
        data = _get_form_data(request.form)

        if not data["nome_ajustado"]:
            flash('O campo "Nome Ajustado" é obrigatório.', 'danger')
            return redirect(url_for('parceiro.gestao_parceiros'))

        # --- LÓGICA DA API (AGORA USANDO /api/user) ---
        try:
            sucesso_api, erro_api = _cadastrar_parceiro_embedded(data)
            
            if not sucesso_api:
                flash(f'Erro ao cadastrar parceiro (usuário) no sistema Embedded: {erro_api}', 'danger')
                return redirect(url_for('parceiro.gestao_parceiros'))

            # 2. Se a API funcionou, salva no banco local
            error_db = db.add_parceiro(**data)
            
            if error_db:
                flash(f'Parceiro salvo na API, mas falhou ao salvar localmente: {error_db}', 'danger')
            else:
                flash('Parceiro criado com sucesso (Sincronizado com Embedded)!', 'success')
        
        except Exception as e:
            flash(f'Um erro inesperado ocorreu: {e}', 'danger')
            
        return redirect(url_for('parceiro.gestao_parceiros'))

    # Lógica para o método GET (Visualização e Filtro)
    tipo_filtro = request.args.get('tipo') or None
    status_filtro = request.args.get('status')
    data_entrada_min_filtro = request.args.get('data_entrada_min') or None
    data_saida_max_filtro = request.args.get('data_saida_max') or None
    
    parceiros = db.get_all_parceiros(
        tipo=tipo_filtro,
        status=status_filtro, 
        data_entrada_min=data_entrada_min_filtro,
        data_saida_max=data_saida_max_filtro
    )
    
    status_filtro_display = status_filtro if status_filtro is not None else '' 
    
    return render_template(
        'parceiro/parceiros.html',
        active_page='parceiros_gestao',
        parceiros=parceiros,
        tipo_filtro=tipo_filtro,
        status_filtro=status_filtro_display, 
        data_entrada_min_filtro=data_entrada_min_filtro,
        data_saida_max_filtro=data_saida_max_filtro
    )

@parceiro_bp.route('/editar/<int:parceiro_id>', methods=['POST'])
def editar_parceiro(parceiro_id):
    # NOTA: A lógica de edição (requests.put ou requests.patch)
    # precisará ser implementada aqui também, seguindo o mesmo padrão.
    data = _get_form_data(request.form, sufixo="_edit")

    if not data["nome_ajustado"]:
        flash('O campo "Nome Ajustado" é obrigatório para a edição.', 'danger')
    else:
        _, error = db.update_parceiro(parceiro_id, **data)
        if error:
            flash(f'Erro ao atualizar parceiro: {error}', 'danger')
        else:
            flash('Parceiro atualizado com sucesso!', 'success')

    return redirect(url_for('parceiro.gestao_parceiros'))

@parceiro_bp.route('/deletar/<int:parceiro_id>', methods=['POST'])
def deletar_parceiro(parceiro_id):
    # NOTA: A lógica de deleção (requests.delete)
    # precisará ser implementada aqui também.
    
    confirmation_password = request.form.get('confirmation_password')
    if confirmation_password != DELETE_PASSWORD:
        flash('Senha de confirmação incorreta.', 'danger')
        return redirect(url_for('parceiro.gestao_parceiros'))
    
    _, error = db.delete_parceiro(parceiro_id)
    if error:
        flash(f'Erro ao deletar parceiro: {error}', 'danger')
    else:
        flash('Parceiro deletado permanentemente com sucesso!', 'success')
    return redirect(url_for('parceiro.gestao_parceiros'))