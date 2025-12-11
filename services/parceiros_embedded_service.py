import requests
import json
from datetime import datetime
from config import EMBEDDED_API_KEY

# --- CONFIGURAÇÕES DA API (ATUALIZADAS) ---
# Todas as constantes da API ficam aqui
EMBEDDED_API_URL = "https://api.powerembedded.com.br/api/user"
PARCEIROS_INDUSTRIA_GROUP_ID = "3c4761f3-89ef-4642-92ee-b30d214b92d5" 
PARCEIROS_DISTRIBUIDOR_GROUP_ID = "ca8a1c8d-4ac5-44eb-b594-0417ce882e12" 
# -----------------------------

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
        #1: administrador, 2:Contribuidor, 3:Visualizador
        "role": 3,
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
def _cadastrar_usuario_e_buscar_id(data):
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
        get_url = f"{EMBEDDED_API_URL}?email={user_email_param}"
        
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

# --- FUNÇÃO PARA VINCULAR GRUPO (MODIFICADA) ---
def _linkar_usuario_ao_grupo(user_email, parceiro_tipo):
    """Tenta VINCULAR (PUT) um usuário a um grupo com base no tipo de parceiro."""
    
    group_id = None
    if parceiro_tipo == "INDUSTRIA":
        group_id = PARCEIROS_INDUSTRIA_GROUP_ID
    elif parceiro_tipo == "DISTRIBUIDOR":
        group_id = PARCEIROS_DISTRIBUIDOR_GROUP_ID
        
    if not user_email or not group_id:
        return False, f"Email do usuário ou ID do Grupo para o tipo '{parceiro_tipo}' não fornecido/encontrado."

    api_url_link = f"{EMBEDDED_API_URL}/link-groups"
    headers = _get_api_headers()
    
    payload = {
        "userEmail": user_email,
        "groups": [group_id]
    }

    try:
        response = requests.put(api_url_link, headers=headers, json=payload, timeout=10)

        if response.status_code == 200:
            return True, None # Sucesso
        elif response.status_code == 401:
            return False, "API Erro 401 (Link Group): Não Autorizado."
        elif response.status_code == 403:
            return False, "API Erro 403 (Link Group): Proibido. Sua chave não tem permissão para vincular grupos."
        elif response.status_code == 400:
            try:
                error_details = response.json().get("errors", response.text)
            except json.JSONDecodeError:
                error_details = response.text
            return False, f"API Erro 400 (Link Group): {error_details}"
        else:
            return False, f"API Erro {response.status_code} (Link Group): Erro desconhecido."
    
    except requests.exceptions.RequestException as e:
        return False, f"Falha de conexão com a API (Link Group): {e}"


# --- (UPDATE) FUNÇÃO DE ATUALIZAÇÃO NA API ---
def atualizar_usuario(api_user_id, data):
    """Tenta ATUALIZAR (PUT) um usuário existente na API Embedded."""
    
    if not api_user_id:
        print(f"Aviso: Parceiro local não tem 'api_user_id'. Pulando atualização na API.")
        return True, None # Permite a atualização local

    try:
        payload = _build_api_payload(data, api_user_id=api_user_id)
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
def deletar_usuario(email):
    """Tenta DELETAR (DELETE) um usuário existente na API Embedded."""
    
    if not email:
        print(f"Aviso: Parceiro local não tem 'email'. Pulando deleção na API.")
        return True, None # Permite a deleção local

    api_url_delete = f"{EMBEDDED_API_URL}/{email}"
    headers = _get_api_headers()

    try:
        response = requests.delete(api_url_delete, headers=headers, timeout=10)

        if response.status_code in [200, 204, 404]:
            return True, None
        elif response.status_code == 401:
            return False, "API Erro 401: Não Autorizado."
        elif response.status_code == 403:
             return False, "API Erro 403: Proibido. Sua chave não tem permissão para DELETAR usuários."
        elif response.status_code == 400:
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


# --- FUNÇÃO DE ROLLBACK (REVERSÃO) ---
def rollback_criacao_usuario(email):
    """Tenta deletar um usuário da API usando o email."""
    if not email:
        return False
        
    print(f"--- ROLLBACK ---")
    print(f"Tentando deletar usuário '{email}' da API devido à falha na operação.")
    
    api_url_delete = f"{EMBEDDED_API_URL}/{email}"
    headers = _get_api_headers()
    try:
        response = requests.delete(api_url_delete, headers=headers, timeout=5)
        if response.status_code in [200, 204, 404]:
            print(f"ROLLBACK: Sucesso ao deletar '{email}'.")
            return True
        else:
            print(f"ROLLBACK: Falha ao deletar '{email}'. API retornou {response.status_code}.")
            return False
    except Exception as e:
        print(f"ROLLBACK: Exceção ao tentar deletar '{email}': {e}")
        return False

# --- FUNÇÃO PÚBLICA PRINCIPAL (MODIFICADA) ---
# Esta é a única função que a rota de cadastro precisará chamar
def criar_parceiro_completo(data):
    """
    Executa o fluxo completo de cadastro:
    1. Cria usuário (POST) e busca ID (GET)
    2. Vincula ao grupo (PUT) com base no tipo do parceiro.
    Retorna (api_id, erro)
    """
    user_email = data.get('email_gestor')
    parceiro_tipo = data.get('tipo') # <-- NOVO
    
    # 1. Tenta salvar na API (com POST-then-GET)
    api_response, erro_api = _cadastrar_usuario_e_buscar_id(data)
    
    if erro_api:
        return None, erro_api

    # 2. Tenta vincular ao grupo correto
    sucesso_link, erro_link = _linkar_usuario_ao_grupo(user_email, parceiro_tipo) # <-- NOVO
    
    if erro_link:
        # Se falhar ao vincular, desfaz a criação do usuário
        rollback_criacao_usuario(user_email)
        return None, f"Erro ao vincular usuário ao grupo: {erro_link}. O cadastro do usuário foi revertido."
        
    # 3. Se tudo deu certo, retorna o ID do usuário
    api_id = api_response.get('id') if api_response else None
    return api_id, None

# --- (UPDATE) FUNÇÃO DE DEFINIR SENHA ---
def definir_senha_usuario(email, nova_senha):
    """Tenta ATUALIZAR (PUT) a senha de um usuário."""
    
    if not email or not nova_senha:
        return False, "Email ou nova senha não fornecidos."

    # Endpoint para mudar a senha
    api_url_change_pass = f"{EMBEDDED_API_URL}/change-password"
    headers = _get_api_headers()
    
    # Payload esperado
    payload = {
        "email": email,
        "password": nova_senha
    }

    try:
        response = requests.put(api_url_change_pass, headers=headers, json=payload, timeout=10)

        # 200 OK é o sucesso
        if response.status_code == 200:
            return True, None
        elif response.status_code == 401:
            return False, "API Erro 401 (ChangePass): Não Autorizado."
        elif response.status_code == 403:
             return False, "API Erro 403 (ChangePass): Proibido. Sua chave não tem permissão para alterar senhas."
        elif response.status_code == 400:
             try:
                error_details = response.json().get("errors", response.text)
             except json.JSONDecodeError:
                error_details = response.text
             return False, f"API Erro 400 (ChangePass): {error_details}"
        else:
            return False, f"API Erro {response.status_code} (ChangePass): Erro desconhecido."

    except requests.exceptions.RequestException as e:
        return False, f"Falha ao conectar na API (ChangePass): {e}"