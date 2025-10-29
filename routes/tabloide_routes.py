# routes/tabloide_routes.py

import pandas as pd
import numpy as np
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
)
import os
import database.tabloide_db as db_tabloide  # Importa o banco de dados de tabloide
# Removido: db_common e db_tabloide_produtos
from utils import allowed_file

# Cria o Blueprint de Tabloide
tabloide_bp = Blueprint(
    'tabloide',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/tabloide'
)

# --- ROTA /upload MOVIDA PARA tabloide_produtos_routes.py ---


@tabloide_bp.route('/download_modelo')
def download_modelo():
    try:
        static_dir = os.path.join(tabloide_bp.root_path, '..', 'static', 'models')
        filename = 'modelo_tabloide.xlsx'
        return send_from_directory(
            static_dir,
            filename,
            as_attachment=True
        )
    except FileNotFoundError:
        flash('Arquivo modelo não encontrado no servidor.', 'danger')
        return redirect(request.referrer or url_for('tabloide.gestao_tabloides'))

@tabloide_bp.route('/gerenciar', methods=['GET', 'POST'])
def gestao_tabloides():
    if request.method == 'POST':
        nome = request.form.get('nome')
        data_inicio = request.form.get('data_inicio')
        data_fim = request.form.get('data_fim')

        if not all([nome, data_inicio, data_fim]):
            flash('Todos os campos são obrigatórios.', 'danger')
        else:
            error = db_tabloide.add_campaign(nome, data_inicio, data_fim)
            if error:
                flash(f'Erro ao criar tabloide: {error}', 'danger')
            else:
                flash('Tabloide criado com sucesso!', 'success')
        return redirect(url_for('tabloide.gestao_tabloides'))

    tabloides = db_tabloide.get_all_campaigns()
    return render_template(
        'tabloide/tabloides.html', 
        active_page='tabloides_gestao', 
        tabloides=tabloides
    )


@tabloide_bp.route('/editar/<int:campaign_id>', methods=['POST'])
def editar_tabloide(campaign_id):
    nome = request.form.get('nome_edit')
    data_inicio = request.form.get('data_inicio_edit')
    data_fim = request.form.get('data_fim_edit')

    if not all([nome, data_inicio, data_fim]):
        flash('Todos os campos são obrigatórios para a edição.', 'danger')
    else:
        _, error = db_tabloide.update_campaign(campaign_id, nome, data_inicio, data_fim)
        if error:
            flash(f'Erro ao atualizar tabloide: {error}', 'danger')
        else:
            flash('Tabloide atualizado com sucesso!', 'success')
    return redirect(url_for('tabloide.gestao_tabloides'))


@tabloide_bp.route('/deletar/<int:campaign_id>', methods=['POST'])
def deletar_tabloide(campaign_id):
    _, error = db_tabloide.delete_campaign(campaign_id)
    if error:
        flash(f'Erro ao desativar tabloide: {error}', 'danger')
    else:
        flash('Tabloide desativado com sucesso!', 'success')
    return redirect(url_for('tabloide.gestao_tabloides'))

# --- ROTAS DE PRODUTOS MOVIDAS PARA tabloide_produtos_routes.py ---