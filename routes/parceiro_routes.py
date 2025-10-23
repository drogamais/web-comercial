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
    
    # Converte 'ativo'/'inativo' para 1/0
    status = 1 if form.get('status') == 'ativo' else 0

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
    return render_template('parceiro/parceiros.html', active_page='parceiros', parceiros=parceiros)

@parceiro_bp.route('/editar/<int:parceiro_id>', methods=['POST'])
def editar_parceiro(parceiro_id):
    # Pega os dados do formulário do modal (que têm sufixo _edit)
    form_data = {key.replace('_edit', ''): value for key, value in request.form.items()}
    
    # Usa a função auxiliar para tratar os dados do formulário de edição
    data = _get_form_data(form_data)

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
    # Esta rota agora apenas realiza o SOFT DELETE (muda status para 0)
    # A função de DB 'delete_parceiro' já faz isso.
    _, error = db.delete_parceiro(parceiro_id)
    if error:
        flash(f'Erro ao desativar parceiro: {error}', 'danger')
    else:
        flash('Parceiro desativado com sucesso!', 'success')
    return redirect(url_for('parceiro.gestao_parceiros'))