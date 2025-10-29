from flask import (
    Blueprint, render_template, request, redirect, url_for, flash
)
import database.parceiro_db as db # Banco de dados de parceiros

# Cria o Blueprint de Parceiros
parceiro_bp = Blueprint(
    'parceiro',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/parceiro' # Prefixo /parceiro
)

def _get_form_data(form):
    """Função auxiliar para pegar dados do formulário e tratar campos vazios."""
    data_entrada = form.get('data_entrada') or None
    data_saida = form.get('data_saida') or None
    
    # CORRIGIDO: Status sempre 1 (ATIVO) para criação, pois o campo foi removido do formulário.
    status = 1 

    return {
        "cnpj": form.get('cnpj') or None,
        "nome_fantasia": form.get('nome_fantasia') or None,
        "tipo": form.get('tipo') or None,
        "razao_social": form.get('razao_social') or None,
        "nome": form.get('nome'),
        "email": form.get('email') or None,
        "telefone": form.get('telefone') or None,
        "data_entrada": data_entrada,
        "data_saida": data_saida,
        "status": status
    }

@parceiro_bp.route('/gerenciar', methods=['GET', 'POST'])
def gestao_parceiros():
    if request.method == 'POST':
        # Usa a função auxiliar para pegar os dados do formulário de criação
        data = _get_form_data(request.form)

        if not data["nome"]:
            flash('O campo "Nome Ajustado" é obrigatório.', 'danger')
        else:
            error = db.add_parceiro(
                data["cnpj"], data["nome_fantasia"], data["tipo"], 
                data["razao_social"], data["nome"], data["email"], 
                data["telefone"], data["data_entrada"], data["data_saida"], 
                data["status"]
            )
            if error:
                flash(f'Erro ao criar parceiro: {error}', 'danger')
            else:
                flash('Parceiro criado com sucesso!', 'success')
        return redirect(url_for('parceiro.gestao_parceiros'))

    # GET: Busca todos os parceiros (ativos e inativos)
    parceiros = db.get_all_parceiros()
    return render_template(
        'parceiro/parceiros.html', 
        active_page='parceiros_gestao', 
        parceiros=parceiros
    )

@parceiro_bp.route('/editar/<int:parceiro_id>', methods=['POST'])
def editar_parceiro(parceiro_id):
    # Pega os dados do formulário do modal (que têm sufixo _edit)
    form_data = {key.replace('_edit', ''): value for key, value in request.form.items()}
    
    # Processamento manual dos dados, forçando status=1
    data_entrada = form_data.get('data_entrada') or None
    data_saida = form_data.get('data_saida') or None
    
    data = {
        "cnpj": form_data.get('cnpj') or None,
        "nome_fantasia": form_data.get('nome_fantasia') or None,
        "tipo": form_data.get('tipo') or None,
        "razao_social": form_data.get('razao_social') or None,
        "nome": form_data.get('nome'),
        "email": form_data.get('email') or None,
        "telefone": form_data.get('telefone') or None,
        "data_entrada": data_entrada,
        "data_saida": data_saida,
        "status": 1 # CORRIGIDO: Forçar status=1 para o registro que está sendo editado.
    }

    if not data["nome"]:
        flash('O campo "Nome Ajustado" é obrigatório para a edição.', 'danger')
    else:
        _, error = db.update_parceiro(
            parceiro_id,
            data["cnpj"], data["nome_fantasia"], data["tipo"], 
            data["razao_social"], data["nome"], data["email"], 
            data["telefone"], data["data_entrada"], data["data_saida"], 
            data["status"]
        )
        if error:
            flash(f'Erro ao atualizar parceiro: {error}', 'danger')
        else:
            flash('Parceiro atualizado com sucesso!', 'success')
    return redirect(url_for('parceiro.gestao_parceiros'))

@parceiro_bp.route('/deletar/<int:parceiro_id>', methods=['POST'])
def deletar_parceiro(parceiro_id):
    # A função de DB 'delete_parceiro' agora fará um DELETE.
    _, error = db.delete_parceiro(parceiro_id)
    if error:
        flash(f'Erro ao deletar parceiro: {error}', 'danger')
    # MUDANÇA: Mensagem de exclusão permanente
    else:
        flash('Parceiro deletado permanentemente com sucesso!', 'success')
    return redirect(url_for('parceiro.gestao_parceiros'))