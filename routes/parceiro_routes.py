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

@parceiro_bp.route('/gerenciar', methods=['GET', 'POST'])
def gestao_parceiros():
    if request.method == 'POST':
        nome = request.form.get('nome')
        if not nome:
            flash('O nome do parceiro é obrigatório.', 'danger')
        else:
            error = db.add_parceiro(nome)
            if error:
                flash(f'Erro ao criar parceiro: {error}', 'danger')
            else:
                flash('Parceiro criado com sucesso!', 'success')
        return redirect(url_for('parceiro.gestao_parceiros'))

    parceiros = db.get_all_parceiros()
    return render_template('parceiro/parceiros.html', active_page='parceiros', parceiros=parceiros)

@parceiro_bp.route('/editar/<int:parceiro_id>', methods=['POST'])
def editar_parceiro(parceiro_id):
    nome = request.form.get('nome_edit')
    if not nome:
        flash('O nome do parceiro é obrigatório para a edição.', 'danger')
    else:
        _, error = db.update_parceiro(parceiro_id, nome)
        if error:
            flash(f'Erro ao atualizar parceiro: {error}', 'danger')
        else:
            flash('Parceiro atualizado com sucesso!', 'success')
    return redirect(url_for('parceiro.gestao_parceiros'))

@parceiro_bp.route('/deletar/<int:parceiro_id>', methods=['POST'])
def deletar_parceiro(parceiro_id):
    _, error = db.delete_parceiro(parceiro_id)
    if error:
        flash(f'Erro ao desativar parceiro: {error}', 'danger')
    else:
        flash('Parceiro desativado com sucesso!', 'success')
    return redirect(url_for('parceiro.gestao_parceiros'))