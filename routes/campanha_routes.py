# routes/campanha_routes.py

import pandas as pd
import numpy as np
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
)
import os
import database.campanha_db as db_campanha # Para gerenciar campanhas
import database.parceiro_db as db_parceiro # Para buscar parceiros
import services.parceiros_embedded_service as api_service # Importar serviço de API
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
        parceiro_id = request.form.get('parceiro_id') or None 
        
        if not all([nome, data_inicio, data_fim]):
            flash('Campos Nome, Início e Fim são obrigatórios.', 'danger')
        else:
            # MODIFICADO: Passa o parceiro_id para a função do DB
            error = db_campanha.add_campaign(nome, data_inicio, data_fim, parceiro_id)
            if error: 
                flash(f'Erro ao criar campanha: {error}', 'danger')
            else:
                # NOVO: Lógica de linkagem à API no momento da criação da Campanha
                if parceiro_id:
                    parceiro = db_parceiro.get_parceiro_by_id(parceiro_id)
                    email = parceiro.get('email_gestor') if parceiro else None
                    if email:
                        _, erro_adicao = api_service.adicionar_usuario_ao_grupo(
                            email, 
                            api_service.PARCEIROS_CAMPANHA_GROUP_ID
                        )
                        if erro_adicao:
                            flash(f'Campanha criada, mas falha ao vincular parceiro ao grupo Embedded: {erro_adicao}', 'warning')
                        else:
                            flash('Campanha criada e parceiro vinculado ao grupo com sucesso!', 'success')
                    else:
                        flash('Campanha criada, mas email do parceiro não encontrado para vincular ao grupo Embedded.', 'warning')
                else:
                    flash('Campanha criada com sucesso!', 'success')
        return redirect(url_for('campanha.gestao_campanhas'))
    
    # GET
    campanhas = db_campanha.get_all_campaigns()
    parceiros = db_parceiro.get_all_parceiros() 
    return render_template(
        'campanha/campanhas.html', 
        active_page='campanhas', 
        campanhas=campanhas,
        parceiros=parceiros 
    )

@campanha_bp.route('/editar/<int:campaign_id>', methods=['POST'])
def editar_campanha(campaign_id):
    nome = request.form.get('nome_edit')
    data_inicio = request.form.get('data_inicio_edit')
    data_fim = request.form.get('data_fim_edit')
    parceiro_id_novo = request.form.get('parceiro_id_edit') or None 

    # 1. Obter dados antigos da campanha para a lógica de grupo
    campanha_antiga = db_campanha.get_campaign_by_id(campaign_id)
    parceiro_id_antigo = str(campanha_antiga.get('parceiro_id')) if campanha_antiga and campanha_antiga.get('parceiro_id') else None
    
    # 2. Normalizar o novo ID (o banco de dados aceita string ou None)
    parceiro_id_novo = str(parceiro_id_novo) if parceiro_id_novo else None
    
    # 3. Executar o update no banco de dados (Primeiro o DB para manter integridade)
    if not all([nome, data_inicio, data_fim]):
        flash('Todos os campos são obrigatórios para a edição.', 'danger')
        return redirect(url_for('campanha.gestao_campanhas'))

    _, error = db_campanha.update_campaign(campaign_id, nome, data_inicio, data_fim, parceiro_id_novo)
    
    if error: 
        flash(f'Erro ao atualizar campanha: {error}', 'danger')
        return redirect(url_for('campanha.gestao_campanhas'))
    
    # 4. Lógica de atualização de grupo na API Embedded
    
    # a) VERIFICAR REMOÇÃO DO PARCEIRO ANTIGO (se o ID mudou ou foi removido)
    if parceiro_id_antigo and parceiro_id_antigo != parceiro_id_novo:
        parceiro_antigo = db_parceiro.get_parceiro_by_id(parceiro_id_antigo)
        email_antigo = parceiro_antigo.get('email_gestor') if parceiro_antigo else None
        
        if email_antigo:
            # Tenta remover o parceiro antigo do grupo de Campanha
            _, erro_remocao = api_service.remover_usuario_do_grupo(
                email_antigo, 
                api_service.PARCEIROS_CAMPANHA_GROUP_ID
            )
            if erro_remocao:
                flash(f'Aviso: Falha ao remover parceiro antigo do grupo Embedded: {erro_remocao}', 'warning')
    
    # b) VERIFICAR ADIÇÃO DO NOVO PARCEIRO (se o ID mudou ou um foi adicionado)
    if parceiro_id_novo and parceiro_id_novo != parceiro_id_antigo:
        parceiro_novo = db_parceiro.get_parceiro_by_id(parceiro_id_novo)
        email_novo = parceiro_novo.get('email_gestor') if parceiro_novo else None
        
        if email_novo:
            # Tenta adicionar o novo parceiro ao grupo de Campanha
            _, erro_adicao = api_service.adicionar_usuario_ao_grupo(
                email_novo, 
                api_service.PARCEIROS_CAMPANHA_GROUP_ID
            )
            if erro_adicao:
                flash(f'Aviso: Falha ao adicionar novo parceiro ao grupo Embedded: {erro_adicao}', 'warning')
                
    flash('Campanha atualizada com sucesso!', 'success')
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
