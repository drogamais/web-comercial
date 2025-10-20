import pandas as pd
import numpy as np
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, current_app
)
import database.tabloide_db as db # Importa o banco de dados de tabloide
from utils import allowed_file # Reutiliza a função de utils

# Cria o Blueprint de Tabloide
tabloide_bp = Blueprint(
    'tabloide', 
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/tabloide' # Prefixo /tabloide
)

@tabloide_bp.route('/upload', methods=['GET', 'POST'])
def upload_page():
    if request.method == 'POST':
        tabloide_id = request.form.get('tabloide') # Modificado
        if not tabloide_id:
            flash('Por favor, selecione um tabloide.', 'danger')
            return redirect(url_for('tabloide.upload_page'))

        file = request.files.get('file')
        if not file or file.filename == '':
            flash('Nenhum arquivo selecionado.', 'danger')
            return redirect(url_for('tabloide.upload_page'))

        if file and allowed_file(file.filename):
            try:
                # ----------------- MAPA DE COLUNAS -----------------
                column_map = {
                    'GTIN': 'codigo_barras', 
                    'DESCRIÇÃO': 'descricao', 
                    'LABORATÓRIO': 'laboratorio',
                    'PREÇO NORMAL': 'preco_normal', 
                    'PREÇO DESCONTO GERAL': 'preco_desconto',
                    'PREÇO DESCONTO CLIENTE+': 'preco_desconto_cliente', # Chave sem espaço antes do +
                    'TIPO DE REGRA': 'tipo_regra'
                    # A coluna "TIPO DE PREÇO" não é necessária, então é ignorada.
                }
                
                # Lê o Excel
                df = pd.read_excel(file)
                
                # --- LÓGICA DE LIMPEZA ATUALIZADA (FINAL) ---
                df.columns = (
                    df.columns.astype(str)
                    .str.replace(r'\s+', ' ', regex=True)   # Consolida TODOS os tipos de whitespace
                    .str.replace(r'\s\+', '+', regex=True) # Remove espaço antes do +
                    .str.strip()                          # Limpa as bordas
                    .str.upper()                          # (NOVO) Força tudo para MAIÚSCULO
                )
                
                # Agora faz o rename com os nomes limpos
                df = df.rename(columns=column_map)
                
                # Substitui NaN por None (NULL para o banco)
                df = df.replace({np.nan: None})
                
                # Converte colunas numéricas que podem ter vindo como texto (ex: ' - ')
                cols_to_numeric = ['preco_normal', 'preco_desconto', 'preco_desconto_cliente']
                for col in cols_to_numeric:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce').replace({np.nan: None})

                required_cols = list(column_map.values()) 
                
                # Verifica se todas as colunas renomeadas existem
                if not all(col in df.columns for col in required_cols):
                    missing = [col for col in required_cols if col not in df.columns]
                    # Esta é a mensagem de erro que você está vendo
                    flash(f'A planilha não contém todas as colunas esperadas. Faltando: {", ".join(missing)}', 'danger')
                    return redirect(url_for('tabloide.upload_page'))

                # ----------------- INSERÇÃO DE PRODUTOS ATUALIZADA -----------------
                produtos_para_inserir = [
                    (tabloide_id, 
                     row.get('codigo_barras'), row.get('descricao'), row.get('laboratorio'),
                     row.get('preco_normal'), row.get('preco_desconto'), 
                     row.get('preco_desconto_cliente'), row.get('tipo_regra')
                    )
                    for _, row in df.iterrows()
                ]
                
                if produtos_para_inserir:
                    rowcount, error = db.add_products_bulk(produtos_para_inserir) # Modificado
                    if error: flash(f'Erro ao salvar produtos: {error}', 'danger')
                    else: flash(f'{rowcount} produtos processados e salvos com sucesso!', 'success')
                else:
                    flash('Nenhum produto encontrado na planilha.', 'warning')
            except Exception as e:
                flash(f'Ocorreu um erro ao processar o arquivo: {e}', 'danger')
            return redirect(url_for('tabloide.upload_page'))

    tabloides = db.get_active_campaigns_for_upload() # Modificado
    return render_template('tabloide/upload_tabloide.html', active_page='upload', tabloides=tabloides) # Modificado

@tabloide_bp.route('/gerenciar', methods=['GET', 'POST'])
def gestao_tabloides(): # Modificado
    if request.method == 'POST':
        nome = request.form.get('nome')
        data_inicio = request.form.get('data_inicio')
        data_fim = request.form.get('data_fim')
        if not all([nome, data_inicio, data_fim]):
            flash('Todos os campos são obrigatórios.', 'danger')
        else:
            error = db.add_campaign(nome, data_inicio, data_fim) # Modificado
            if error: flash(f'Erro ao criar tabloide: {error}', 'danger')
            else: flash('Tabloide criado com sucesso!', 'success')
        return redirect(url_for('tabloide.gestao_tabloides')) # Modificado
    tabloides = db.get_all_campaigns() # Modificado
    return render_template('tabloide/tabloides.html', active_page='tabloides', tabloides=tabloides) # Modificado

@tabloide_bp.route('/editar/<int:campaign_id>', methods=['POST'])
def editar_tabloide(campaign_id): # Modificado
    nome = request.form.get('nome_edit')
    data_inicio = request.form.get('data_inicio_edit')
    data_fim = request.form.get('data_fim_edit')
    if not all([nome, data_inicio, data_fim]):
        flash('Todos os campos são obrigatórios para a edição.', 'danger')
    else:
        _, error = db.update_campaign(campaign_id, nome, data_inicio, data_fim) # Modificado
        if error: flash(f'Erro ao atualizar tabloide: {error}', 'danger')
        else: flash('Tabloide atualizado com sucesso!', 'success')
    return redirect(url_for('tabloide.gestao_tabloides')) # Modificado

@tabloide_bp.route('/deletar/<int:campaign_id>', methods=['POST'])
def deletar_tabloide(campaign_id): # Modificado
    _, error = db.delete_campaign(campaign_id) # Modificado
    if error: flash(f'Erro ao desativar tabloide: {error}', 'danger')
    else: flash('Tabloide desativado com sucesso!', 'success')
    return redirect(url_for('tabloide.gestao_tabloides')) # Modificado

@tabloide_bp.route('/<int:campanha_id>/produtos')
def produtos_por_tabloide(campanha_id): # Modificado
    tabloide = db.get_campaign_by_id(campanha_id) # Modificado
    if not tabloide:
        flash('Tabloide não encontrado.', 'danger')
        return redirect(url_for('tabloide.gestao_tabloides')) # Modificado
    produtos = db.get_products_by_campaign_id(campanha_id) # Modificado
    return render_template('tabloide/produtos_tabloide.html', active_page='tabloides', tabloide=tabloide, produtos=produtos) # Modificado

@tabloide_bp.route('/<int:campanha_id>/produtos/adicionar', methods=['POST'])
def adicionar_produto(campanha_id): # Modificado
    try:
        # ----------------- DADOS DO PRODUTO ATUALIZADOS -----------------
        dados_produto = (
            campanha_id, 
            request.form.get('codigo_barras'), 
            request.form.get('descricao'),
            request.form.get('laboratorio') or None,
            request.form.get('preco_normal') or None,
            request.form.get('preco_desconto') or None,
            request.form.get('preco_desconto_cliente') or None,
            request.form.get('tipo_regra') or None
        )
        _, error = db.add_single_product(dados_produto) # Modificado
        if error: flash(f'Erro ao adicionar produto: {error}', 'danger')
        else: flash('Novo produto adicionado com sucesso!', 'success')
    except Exception as e:
        flash(f'Ocorreu um erro inesperado: {e}', 'danger')
    return redirect(url_for('tabloide.produtos_por_tabloide', campanha_id=campanha_id)) # Modificado

@tabloide_bp.route('/<int:campanha_id>/produtos/atualizar', methods=['POST'])
def atualizar_produtos(campanha_id): # Modificado
    selecionados = request.form.getlist('selecionado')
    if not selecionados:
        flash('Nenhum produto selecionado para atualizar.', 'warning')
        return redirect(url_for('tabloide.produtos_por_tabloide', campanha_id=campanha_id))
    
    # ----------------- CAMPOS DE ATUALIZAÇÃO ATUALIZADOS -----------------
    produtos_para_atualizar = [
        (request.form.get(f'codigo_barras_{pid}'), 
         request.form.get(f'descricao_{pid}'),
         request.form.get(f'laboratorio_{pid}') or None,
         request.form.get(f'preco_normal_{pid}') or None,
         request.form.get(f'preco_desconto_{pid}') or None,
         request.form.get(f'preco_desconto_cliente_{pid}') or None,
         request.form.get(f'tipo_regra_{pid}') or None, 
         pid)
        for pid in selecionados
    ]
    rowcount, error = db.update_products_in_bulk(produtos_para_atualizar) # Modificado
    if error: flash(f'Erro ao atualizar produtos: {error}', 'danger')
    else: flash(f'{rowcount} produto(s) atualizado(s) com sucesso!', 'success')
    return redirect(url_for('tabloide.produtos_por_tabloide', campanha_id=campanha_id))

@tabloide_bp.route('/<int:campanha_id>/produtos/deletar', methods=['POST'])
def deletar_produtos(campanha_id): # Modificado
    selecionados = request.form.getlist('selecionado')
    if not selecionados:
        flash('Nenhum produto selecionado para deletar.', 'warning')
        return redirect(url_for('tabloide.produtos_por_tabloide', campanha_id=campanha_id))
    rowcount, error = db.delete_products_in_bulk(selecionados) # Modificado
    if error: flash(f'Erro ao deletar produtos: {error}', 'danger')
    else: flash(f'{rowcount} produto(s) deletado(s) com sucesso!', 'success')
    return redirect(url_for('tabloide.produtos_por_tabloide', campanha_id=campanha_id))