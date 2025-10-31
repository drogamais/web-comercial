# routes/campanha_routes.py

import pandas as pd
import numpy as np
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
)
import os
import database.campanha_db as db_campanha # Para gerenciar campanhas
import database.parceiro_db as db_parceiro # Para buscar parceiros
from utils import DELETE_PASSWORD

# Cria o Blueprint de Campanha com prefixo de URL
campanha_bp = Blueprint(
    'campanha', 
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/campanha'
)

@campanha_bp.route('/download_modelo')
def download_modelo():
    try:
        static_dir = os.path.join(campanha_bp.root_path, '..', 'static', 'core', 'models')
        filename = 'modelo_campanha.xlsx'
        return send_from_directory(
            static_dir,
            filename,
            as_attachment=True
        )
    except FileNotFoundError:
        flash('Arquivo modelo não encontrado no servidor.', 'danger')
        return redirect(request.referrer or url_for('campanha.gestao_campanhas'))

@campanha_bp.route('/gerenciar', methods=['GET', 'POST'])
def gestao_campanhas():
    if request.method == 'POST':
        nome = request.form.get('nome')
        data_inicio = request.form.get('data_inicio')
        data_fim = request.form.get('data_fim')
        parceiro_id = request.form.get('parceiro_id') or None # <-- ADICIONADO
        
        if not all([nome, data_inicio, data_fim]):
            flash('Campos Nome, Início e Fim são obrigatórios.', 'danger')
        else:
            # MODIFICADO: Passa o parceiro_id para a função do DB
            error = db_campanha.add_campaign(nome, data_inicio, data_fim, parceiro_id)
            if error: flash(f'Erro ao criar campanha: {error}', 'danger')
            else: flash('Campanha criada com sucesso!', 'success')
        return redirect(url_for('campanha.gestao_campanhas'))
    
    # GET
    campanhas = db_campanha.get_all_campaigns()
    parceiros = db_parceiro.get_all_parceiros() # <-- ADICIONADO
    return render_template(
        'campanha/campanhas.html', 
        active_page='campanhas', 
        campanhas=campanhas,
        parceiros=parceiros # <-- ADICIONADO
    )

@campanha_bp.route('/editar/<int:campaign_id>', methods=['POST'])
def editar_campanha(campaign_id):
    nome = request.form.get('nome_edit')
    data_inicio = request.form.get('data_inicio_edit')
    data_fim = request.form.get('data_fim_edit')
    parceiro_id = request.form.get('parceiro_id_edit') or None # <-- ADICIONADO
    
    if not all([nome, data_inicio, data_fim]):
        flash('Todos os campos são obrigatórios para a edição.', 'danger')
    else:
        # MODIFICADO: Passa o parceiro_id para a função do DB
        _, error = db_campanha.update_campaign(campaign_id, nome, data_inicio, data_fim, parceiro_id)
        if error: flash(f'Erro ao atualizar campanha: {error}', 'danger')
        else: flash('Campanha atualizada com sucesso!', 'success')
    return redirect(url_for('campanha.gestao_campanhas'))


@campanha_bp.route('/deletar/<int:campaign_id>', methods=['POST'])
def deletar_campanha(campaign_id):
    # --- NOVO: Verificação de Senha ---
    confirmation_password = request.form.get('confirmation_password')
    if confirmation_password != DELETE_PASSWORD:
        flash(f'Senha de confirmação incorreta.', 'danger')
        return redirect(url_for('campanha.gestao_campanhas'))
    # --- FIM NOVO ---
    
    _, error = db_campanha.delete_campaign(campaign_id)
    if error: flash(f'Erro ao deletar campanha: {error}', 'danger')
    else: flash('Campanha deletada permanentemente com sucesso!', 'success')
    return redirect(url_for('campanha.gestao_campanhas'))