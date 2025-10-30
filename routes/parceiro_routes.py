from flask import Blueprint, render_template, request, redirect, url_for, flash
import database.parceiro_db as db

# Campos principais do parceiro - AJUSTADOS PARA O SEU SCHEMA FINAL
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
    data["status"] = 1  # Sempre ativo
    return data

@parceiro_bp.route('/gerenciar', methods=['GET', 'POST'])
def gestao_parceiros():
    if request.method == 'POST':
        data = _get_form_data(request.form)

        if not data["nome_ajustado"]:
            flash('O campo "Nome Ajustado" é obrigatório.', 'danger')
        else:
            error = db.add_parceiro(**data)
            if error:
                flash(f'Erro ao criar parceiro: {error}', 'danger')
            else:
                flash('Parceiro criado com sucesso!', 'success')
        return redirect(url_for('parceiro.gestao_parceiros'))

    parceiros = db.get_all_parceiros()
    return render_template(
        'parceiro/parceiros.html',
        active_page='parceiros_gestao',
        parceiros=parceiros
    )

@parceiro_bp.route('/editar/<int:parceiro_id>', methods=['POST'])
def editar_parceiro(parceiro_id):
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
    _, error = db.delete_parceiro(parceiro_id)
    if error:
        flash(f'Erro ao deletar parceiro: {error}', 'danger')
    else:
        flash('Parceiro deletado permanentemente com sucesso!', 'success')
    return redirect(url_for('parceiro.gestao_parceiros'))