# routes/parceiro_routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
import database.parceiro_db as db
from utils import DELETE_PASSWORD
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

def _get_api_headers():
    """Retorna os headers de autenticação padrão para a API."""
    return {
        "X-API-Key": EMBEDDED_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

def _build_api_payload(data, api_user_id=None):
    """Monta o payload de dados para a API a partir dos dados do formulário."""
    try:
        expiration_date_iso = None
        if data.get("data_saida"):
            dt_end = datetime.strptime(data.get("data_saida"), '%Y-%m-%d')
            expiration_date_iso = dt_end.strftime('%Y-%m-%dT00:00:00Z')
    
    except ValueError as e:
        raise ValueError(f"Formato de data inválido. Use AAAA-MM-DD. Erro: {e}")

    user_email = data.get("email_gestor")
    user_name = data.get("nome_fantasia") 

    if not user_email:
        raise ValueError("O campo 'E-mail Gestor' é obrigatório para a API.")
    if not user_name:
        raise ValueError("O campo 'Nome Fantasia' é obrigatório para a API.")

    payload = {
        "name": user_name,
        "email": user_email,
        "role": 1,
        "department": data.get("tipo"),
        "expirationDate": expiration_date_iso,
        "reportLandingPage": None, "windowsAdUser": None, "bypassFirewall": False,
        "canEditReport": False, "canCreateReport": False, "canOverwriteReport": False,
        "canRefreshDataset": False, "canCreateSubscription": False, "canDownloadPbix": False,
        "canExportReportWithHiddenPages": False, "canCreateNewUsers": False,
        "canStartCapacityByDemand": False, "canDisplayVisualHeaders": True,
        "canExportReportOtherPages": False, "accessReportAnyTime": True,
        "sendWelcomeEmail": True
    }
    
    if api_user_id:
        payload["id"] = api_user_id

    return payload

# --- (CREATE) FUNÇÃO DE CADASTRO NA API ---
def _cadastrar_parceiro_embedded(data):
    """
    Tenta CRIAR (POST) um novo usuário, e depois BUSCAR (GET com filtro)
    para capturar o ID retornado.
    """
    headers = _get_api_headers()
    try:
        payload = _build_api_payload(data, api_user_id=None) 
    except ValueError as e:
        return None, str(e) 

    try:
        # --- PASSO 1: Tenta CRIAR o usuário (POST) ---
        response = requests.post(EMBEDDED_API_URL, headers=headers, json=payload, timeout=10)

        if response.status_code != 200:
            if response.status_code == 401:
                return None, "API Erro 401: Não Autorizado. Verifique sua Chave de API (Token)."
            try:
                error_details = response.json().get("message", response.text)
            except json.JSONDecodeError:
                error_details = response.text
            return None, f"API Embedded Erro {response.status_code} (POST): {error_details}"

        # --- PASSO 2: SUCESSO! Agora busca o usuário (GET) usando o filtro de email ---
        user_email_param = payload['email']
        get_url = f"{EMBEDDED_API_URL}?email={user_email_param}" # Usa o endpoint de LISTA com filtro
        
        get_response = requests.get(get_url, headers=headers, timeout=10)

        if get_response.status_code == 200:
            try:
                response_data = get_response.json()
                user_list = response_data.get('data')

                if user_list and len(user_list) > 0:
                    user_data = user_list[0]
                    api_id = user_data.get('id')
                    
                    if api_id:
                        return {"id": api_id}, None
                    else:
                        return None, "API criou e listou o usuário, mas ele veio sem 'id' no JSON."
                else:
                    return None, f"API criou o usuário (POST 200), mas a busca (GET) por '{user_email_param}' não o encontrou."

            except (json.JSONDecodeError, KeyError, IndexError) as e:
                return None, f"API criou o usuário, mas a resposta GET foi inválida: {e}"
        else:
            return None, f"API criou o usuário (POST 200 OK), mas falhou ao buscá-lo (GET {get_response.status_code}). Verifique as permissões da sua chave."

    except requests.exceptions.RequestException as e:
        return None, f"Falha de conexão com a API: {e}"

# --- (UPDATE) FUNÇÃO DE ATUALIZAÇÃO NA API ---
def _atualizar_parceiro_embedded(parceiro_id, new_data):
    """Tenta ATUALIZAR (PUT) um usuário existente na API Embedded."""
    
    parceiro_atual = db.get_parceiro_by_id(parceiro_id)
    if not parceiro_atual:
        return False, "Parceiro não encontrado no banco de dados local."
    
    api_user_id = parceiro_atual.get('api_user_id')
    if not api_user_id:
        print(f"Aviso: Parceiro local ID {parceiro_id} não tem 'api_user_id'. Pulando atualização na API.")
        return True, None 

    try:
        payload = _build_api_payload(new_data, api_user_id=api_user_id)
        headers = _get_api_headers()
    except ValueError as e:
        return False, str(e)

    api_url_update = EMBEDDED_API_URL # PUT /api/user

    try:
        response = requests.put(api_url_update, headers=headers, json=payload, timeout=10)

        if response.status_code in [200, 204]:
            return True, None
        elif response.status_code == 401:
            return False, "API Erro 401: Não Autorizado."
        elif response.status_code == 403:
             return False, "API Erro 403: Proibido. Sua chave não tem permissão para ATUALIZAR (PUT) usuários."
        elif response.status_code == 404:
            return False, f"API Erro 404: Usuário com ID '{api_user_id}' não encontrado na API."
        else:
            try:
                error_details = response.json().get("message", response.text)
            except json.JSONDecodeError:
                error_details = response.text
            return False, f"API Embedded Erro {response.status_code} (PUT): {error_details}"

    except requests.exceptions.RequestException as e:
        return False, f"Falha ao conectar na API Embedded: {e}"

# --- (DELETE) FUNÇÃO DE DELEÇÃO NA API ---
def _deletar_parceiro_embedded(parceiro_id):
    """Tenta DELETAR (DELETE) um usuário existente na API Embedded."""
    
    parceiro = db.get_parceiro_by_id(parceiro_id)
    if not parceiro:
        return False, "Parceiro não encontrado no banco local."
    
    # --- CORREÇÃO APLICADA AQUI ---
    # A API espera o EMAIL na rota de DELETE, não o ID.
    email = parceiro.get('email_gestor')
    
    if not email:
        # Se não tem email, não podemos deletar na API.
        print(f"Aviso: Parceiro local ID {parceiro_id} não tem 'email'. Pulando deleção na API.")
        return True, None # Permite a deleção local

    # Usa o email como identificador
    identificador_api = email 
    # -------------------------------

    api_url_delete = f"{EMBEDDED_API_URL}/{identificador_api}"
    headers = _get_api_headers()

    try:
        response = requests.delete(api_url_delete, headers=headers, timeout=10)

        if response.status_code in [200, 204]:
            return True, None
        elif response.status_code == 401:
            return False, "API Erro 401: Não Autorizado."
        elif response.status_code == 403:
             return False, "API Erro 403: Proibido. Sua chave não tem permissão para DELETAR usuários."
        elif response.status_code == 404:
             # O erro 400 que você viu antes agora será 404 (provavelmente)
             # ou continuará 400 se o formato do email for inválido.
            return True, None # Não existe mais na API, sucesso
        elif response.status_code == 400:
            # Captura o erro 400 que você viu (caso o email esteja errado)
            try:
                error_details = response.json().get("errors", response.text)
            except json.JSONDecodeError:
                error_details = response.text
            return False, f"API Embedded Erro 400 (DELETE): {error_details}"
        else:
            try:
                error_details = response.json().get("message", response.text)
            except json.JSONDecodeError:
                error_details = response.text
            return False, f"API Embedded Erro {response.status_code} (DELETE): {error_details}"

    except requests.exceptions.RequestException as e:
        return False, f"Falha ao conectar na API Embedded: {e}"


# --- ROTA DE GESTÃO (GET e POST/CREATE) ---
@parceiro_bp.route('/gerenciar', methods=['GET', 'POST'])
def gestao_parceiros():
    if request.method == 'POST':
        data = _get_form_data(request.form)

        if not data["nome_ajustado"]:
            flash('O campo "Nome Ajustado" é obrigatório.', 'danger')
            return redirect(url_for('parceiro.gestao_parceiros'))

        try:
            api_response, erro_api = _cadastrar_parceiro_embedded(data)
            
            if erro_api:
                flash(f'Erro ao cadastrar parceiro na API Embedded: {erro_api}', 'danger')
                return redirect(url_for('parceiro.gestao_parceiros'))

            api_id = None
            if api_response:
                api_id = api_response.get('id')
            
            if not api_id:
                flash(f'API criou o usuário, mas não foi possível extrair um ID. O parceiro será salvo localmente sem o ID da API.', 'warning')
            
            data['api_user_id'] = api_id 
            
            error_db = db.add_parceiro(**data)
            
            if error_db:
                flash(f'Parceiro salvo na API, mas falhou ao salvar localmente: {error_db}', 'danger')
            else:
                flash('Parceiro criado com sucesso (Sincronizado com Embedded)!', 'success')
        
        except Exception as e:
            flash(f'Um erro inesperado ocorreu: {e}', 'danger')
            
        return redirect(url_for('parceiro.gestao_parceiros'))

    # --- LÓGICA GET (exibição) ---
    (parceiros, tipo_filtro, status_filtro_display, 
     data_entrada_min_filtro, data_saida_max_filtro) = _get_parceiros_filtrados(request)
    
    return render_template(
        'parceiro/parceiros.html',
        active_page='parceiros_gestao',
        parceiros=parceiros,
        tipo_filtro=tipo_filtro,
        status_filtro=status_filtro_display, 
        data_entrada_min_filtro=data_entrada_min_filtro,
        data_saida_max_filtro=data_saida_max_filtro
    )

def _get_parceiros_filtrados(request_obj):
    """Função auxiliar para buscar parceiros filtrados (usado no GET)."""
    tipo_filtro = request_obj.args.get('tipo') or None
    status_filtro = request_obj.args.get('status')
    data_entrada_min_filtro = request_obj.args.get('data_entrada_min') or None
    data_saida_max_filtro = request_obj.args.get('data_saida_max') or None
    
    parceiros = db.get_all_parceiros(
        tipo=tipo_filtro,
        status=status_filtro, 
        data_entrada_min=data_entrada_min_filtro,
        data_saida_max=data_saida_max_filtro
    )
    
    status_filtro_display = status_filtro if status_filtro is not None else '' 
    return (parceiros, tipo_filtro, status_filtro_display, 
            data_entrada_min_filtro, data_saida_max_filtro)


# --- ROTA DE EDIÇÃO (UPDATE) ---
@parceiro_bp.route('/editar/<int:parceiro_id>', methods=['POST'])
def editar_parceiro(parceiro_id):
    
    data = _get_form_data(request.form, sufixo="_edit")

    if not data["nome_ajustado"]:
        flash('O campo "Nome Ajustado" é obrigatório para a edição.', 'danger')
        return redirect(url_for('parceiro.gestao_parceiros'))

    try:
        sucesso_api, erro_api = _atualizar_parceiro_embedded(parceiro_id, data)

        if not sucesso_api:
            flash(f'Erro ao atualizar parceiro na API Embedded: {erro_api}', 'danger')
            return redirect(url_for('parceiro.gestao_parceiros'))

        _, error_db = db.update_parceiro(parceiro_id, **data)
        
        if error_db:
            flash(f'Parceiro atualizado na API, mas falhou ao salvar localmente: {error_db}', 'danger')
        else:
            flash('Parceiro atualizado com sucesso (Sincronizado com Embedded)!', 'success')

    except Exception as e:
        flash(f'Um erro inesperado ocorreu ao editar: {e}', 'danger')

    return redirect(url_for('parceiro.gestao_parceiros'))


# --- ROTA DE DELEÇÃO (DELETE) ---
@parceiro_bp.route('/deletar/<int:parceiro_id>', methods=['POST'])
def deletar_parceiro(parceiro_id):
    
    confirmation_password = request.form.get('confirmation_password')
    if confirmation_password != DELETE_PASSWORD:
        flash('Senha de confirmação incorreta.', 'danger')
        return redirect(url_for('parceiro.gestao_parceiros'))
    
    try:
        sucesso_api, erro_api = _deletar_parceiro_embedded(parceiro_id)
        
        if not sucesso_api:
            flash(f'Erro ao deletar parceiro na API Embedded: {erro_api}', 'danger')
            return redirect(url_for('parceiro.gestao_parceiros'))

        _, error_db = db.delete_parceiro(parceiro_id)
        
        if error_db:
            flash(f'Parceiro deletado da API, mas falhou ao deletar localmente: {error_db}', 'danger')
        else:
            flash('Parceiro deletado permanentemente com sucesso (Sincronizado com Embedded)!', 'success')
            
    except Exception as e:
        flash(f'Um erro inesperado ocorreu ao deletar: {e}', 'danger')

    return redirect(url_for('parceiro.gestao_parceiros'))