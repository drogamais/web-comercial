from flask import Blueprint, render_template, request, redirect, url_for, flash
import database.parceiro_db as db
from utils import DELETE_PASSWORD
from config import EMBEDDED_API_KEY
import requests 
import json     
from datetime import datetime 

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

EMBEDDED_API_URL = "https://api.powerembedded.com.br/v1/partner" # <<< URL CORRETA
# ----------------------------------------

def _get_form_data(form, sufixo=""):
    """Extrai e normaliza os dados do formulário."""
    data = {field: (form.get(f"{field}{sufixo}") or None) for field in PARCEIRO_FIELDS}
    data["data_entrada"] = form.get(f"data_entrada{sufixo}") or None
    data["data_saida"] = form.get(f"data_saida{sufixo}") or None
    data["status"] = 1
    return data

# <<< NOVO: Função para chamar a API Embedded >>>
def _cadastrar_parceiro_embedded(data):
    """
    Tenta cadastrar o parceiro na API PowerEmbedded.
    Retorna (True, None) em sucesso.
    Retorna (False, "mensagem_de_erro") em falha.
    """
    
    # --- NOVO: Formatar as datas para o padrão ISO 8601 ---
    # A API espera "2024-10-31T00:00:00Z"
    # O formulário envia "2024-10-31"
    try:
        start_date_iso = None
        if data.get("data_entrada"):
            # Converte '2024-10-31' para um objeto datetime
            dt_start = datetime.strptime(data.get("data_entrada"), '%Y-%m-%d')
            # Formata para '2024-10-31T00:00:00Z' (Padrão Zulu/UTC)
            start_date_iso = dt_start.strftime('%Y-%m-%dT00:00:00Z')

        end_date_iso = None
        if data.get("data_saida"):
            dt_end = datetime.strptime(data.get("data_saida"), '%Y-%m-%d')
            end_date_iso = dt_end.strftime('%Y-%m-%dT00:00:00Z')
    
    except ValueError as e:
        return False, f"Formato de data inválido. Use AAAA-MM-DD. Erro: {e}"
    # --- FIM DA FORMATAÇÃO ---

    # 1. Mapeie os dados (Payload corrigido conforme a API)
    #    Campos da API: name, document, type, trade_name, company_name,
    #    manager, manager_phone, manager_email, start_date, end_date
    payload = {
        "name": data.get("nome_ajustado"),
        "document": data.get("cnpj"),
        "type": data.get("tipo"),
        "trade_name": data.get("nome_fantasia"),
        "company_name": data.get("razao_social"),
        "manager": data.get("gestor"),
        "manager_phone": data.get("telefone_gestor"),
        "manager_email": data.get("email_gestor"),
        "start_date": start_date_iso, # <<< Usando a data formatada
        "end_date": end_date_iso     # <<< Usando a data formatada (pode ser None)
    }

    # 2. Configure os Headers de autenticação (Bearer Token)
    headers = {
        "Authorization": f"Bearer {EMBEDDED_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        # 3. Faça a chamada POST para a API
        response = requests.post(EMBEDDED_API_URL, headers=headers, json=payload, timeout=10)

        # 4. Verifique se a API respondeu com sucesso (201 Created)
        if response.status_code == 201:
            return True, None # Sucesso
        else:
            # A API retornou um erro
            try:
                # Tenta pegar o erro específico da API
                error_details = response.json().get("message", "Erro desconhecido")
            except json.JSONDecodeError:
                error_details = response.text # Se a resposta não for JSON
            
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

        # --- LÓGICA DA API ADICIONADA AQUI ---
        try:
            # 1. Tenta cadastrar na API primeiro
            sucesso_api, erro_api = _cadastrar_parceiro_embedded(data)
            
            if not sucesso_api:
                # Se a API falhar, mostra o erro e NÃO salva no banco local
                flash(f'Erro ao cadastrar parceiro no sistema Embedded: {erro_api}', 'danger')
                return redirect(url_for('parceiro.gestao_parceiros'))

            # 2. Se a API funcionou, salva no banco local
            error_db = db.add_parceiro(**data)
            
            if error_db:
                # Isso é um problema: funcionou na API, mas falhou localmente
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