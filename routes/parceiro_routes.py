from flask import Blueprint, render_template, request, redirect, url_for, flash
import database.parceiro_db as db
from config import DELETE_PASSWORD

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

    # Lógica para o método GET (Visualização e Filtro)
    tipo_filtro = request.args.get('tipo') or None
    status_filtro = request.args.get('status') # '1', '0' ou '' (Todos)
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
    # --- NOVO: Verificação de Senha ---
    confirmation_password = request.form.get('confirmation_password')
    if confirmation_password != DELETE_PASSWORD:
        flash('Senha de confirmação incorreta.', 'danger')
        return redirect(url_for('parceiro.gestao_parceiros'))
    # --- FIM NOVO ---
    
    _, error = db.delete_parceiro(parceiro_id)
    if error:
        flash(f'Erro ao deletar parceiro: {error}', 'danger')
    else:
        flash('Parceiro deletado permanentemente com sucesso!', 'success')
    return redirect(url_for('parceiro.gestao_parceiros'))