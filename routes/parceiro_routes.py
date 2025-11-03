from flask import Blueprint, render_template, request, redirect, url_for, flash
import database.parceiro_db as db
from utils import DELETE_PASSWORD
import services.parceiros_embedded_service as api_service
# -----------

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

def _get_form_data(form, sufixo=""):
    """Extrai e normaliza os dados do formulário."""
    data = {field: (form.get(f"{field}{sufixo}") or None) for field in PARCEIRO_FIELDS}
    data["data_entrada"] = form.get(f"data_entrada{sufixo}") or None
    data["data_saida"] = form.get(f"data_saida{sufixo}") or None
    data["status"] = 1
    return data

# --- ROTA DE GESTÃO (GET e POST/CREATE) ---
@parceiro_bp.route('/gerenciar', methods=['GET', 'POST'])
def gestao_parceiros():
    if request.method == 'POST':
        data = _get_form_data(request.form)
        user_email_para_api = data.get('email_gestor') # Guardamos para o rollback

        if not data["nome_ajustado"]:
            flash('O campo "Nome Ajustado" é obrigatório.', 'danger')
            return redirect(url_for('parceiro.gestao_parceiros'))

        try:
            # 1. Chama o serviço para fazer todo o processo da API
            api_id, erro_api = api_service.criar_parceiro_completo(data)
            
            if erro_api:
                flash(f'Erro ao cadastrar parceiro na API Embedded: {erro_api}', 'danger')
                return redirect(url_for('parceiro.gestao_parceiros'))

            # 2. Se a API funcionou, salva no banco local
            data['api_user_id'] = api_id 
            error_db = db.add_parceiro(**data)
            
            if error_db:
                # Se falhar no banco, desfaz a criação do usuário na API
                api_service.rollback_criacao_usuario(user_email_para_api)
                flash(f'Parceiro salvo na API, mas falhou ao salvar localmente: {error_db}. O cadastro na API foi revertido.', 'danger')
            else:
                flash('Parceiro criado e vinculado ao grupo com sucesso!', 'success')
        
        except Exception as e:
            # Se algo inesperado acontecer, tenta reverter
            api_service.rollback_criacao_usuario(user_email_para_api)
            flash(f'Um erro inesperado ocorreu: {e}. O cadastro foi revertido.', 'danger')
            
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
        
    parceiro_atual = db.get_parceiro_by_id(parceiro_id)
    email_antigo = parceiro_atual.get('email_gestor')
    api_user_id = parceiro_atual.get('api_user_id') # Pega o ID da API
    email_novo = data.get('email_gestor')
    
    if email_antigo != email_novo:
        flash('Não é permitido alterar o "E-mail Gestor". A alteração do email foi ignorada.', 'warning')
        data['email_gestor'] = email_antigo

    try:
        # Chama o serviço de atualização
        sucesso_api, erro_api = api_service.atualizar_usuario(api_user_id, data)

        if not sucesso_api:
            flash(f'Erro ao atualizar parceiro na API Embedded: {erro_api}', 'danger')
            return redirect(url_for('parceiro.gestao_parceiros'))

        # Atualiza o banco local
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
    
    # Pega o email ANTES de deletar o parceiro do banco
    parceiro = db.get_parceiro_by_id(parceiro_id)
    email_para_deletar = parceiro.get('email_gestor') if parceiro else None

    try:
        # Tenta deletar da API primeiro
        sucesso_api, erro_api = api_service.deletar_usuario(email_para_deletar)
        
        if not sucesso_api:
            flash(f'Erro ao deletar parceiro na API Embedded: {erro_api}', 'danger')
            return redirect(url_for('parceiro.gestao_parceiros'))

        # Se a API funcionou, deleta do banco local
        _, error_db = db.delete_parceiro(parceiro_id)
        
        if error_db:
            flash(f'Parceiro deletado da API, mas falhou ao deletar localmente: {error_db}', 'danger')
        else:
            flash('Parceiro deletado permanentemente com sucesso (Sincronizado com Embedded)!', 'success')
            
    except Exception as e:
        flash(f'Um erro inesperado ocorreu ao deletar: {e}', 'danger')

    return redirect(url_for('parceiro.gestao_parceiros'))

# --- ROTA DE DEFINIR SENHA (MODIFICADA) ---
@parceiro_bp.route('/definir-senha/<int:parceiro_id>', methods=['POST'])
def definir_senha(parceiro_id):
    
    nova_senha = request.form.get('nova_senha')
    confirmar_senha = request.form.get('confirmar_senha')

    if not nova_senha or not confirmar_senha:
        flash('Por favor, preencha os dois campos de senha.', 'danger')
        return redirect(url_for('parceiro.gestao_parceiros'))

    if nova_senha != confirmar_senha:
        flash('As senhas não conferem.', 'danger')
        return redirect(url_for('parceiro.gestao_parceiros'))

    parceiro = db.get_parceiro_by_id(parceiro_id)
    if not parceiro or not parceiro.get('email_gestor'):
        flash('Parceiro não encontrado ou sem email cadastrado.', 'danger')
        return redirect(url_for('parceiro.gestao_parceiros'))
        
    email_do_parceiro = parceiro.get('email_gestor')

    try:
        # 1. Chama o serviço para definir a senha na API
        sucesso_api, erro_api = api_service.definir_senha_usuario(email_do_parceiro, nova_senha)

        if not sucesso_api:
            flash(f'Erro ao definir senha na API Embedded: {erro_api}', 'danger')
        else:
            # --- ATUALIZAÇÃO AQUI ---
            # 2. Se a API funcionou, marca a flag no banco local
            error_db = db.set_senha_definida_flag(parceiro_id)
            
            if error_db:
                 flash(f'Senha atualizada na API, mas falhou ao marcar status no banco local: {error_db}', 'warning')
            else:
                 flash(f'Senha do usuário {email_do_parceiro} atualizada com sucesso!', 'success')
            # --- FIM DA ATUALIZAÇÃO ---

    except Exception as e:
        flash(f'Um erro inesperado ocorreu ao definir a senha: {e}', 'danger')

    return redirect(url_for('parceiro.gestao_parceiros'))