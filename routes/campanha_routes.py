import pandas as pd
import numpy as np
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, send_from_directory
)
import os
import database.campanha_db as db # Usamos 'db' para simplificar
from utils import allowed_file # 

# Cria o Blueprint de Campanha com prefixo de URL
campanha_bp = Blueprint(
    'campanha', 
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/campanha' # Todas as rotas aqui começarão com /campanha
)

@campanha_bp.route('/upload', methods=['GET', 'POST'])
def upload_page():
    if request.method == 'POST':
        campanha_id = request.form.get('campanha')
        if not campanha_id:
            flash('Por favor, selecione uma campanha.', 'danger')
            return redirect(url_for('campanha.upload_page'))

        file = request.files.get('file')
        if not file or file.filename == '':
            flash('Nenhum arquivo selecionado.', 'danger')
            return redirect(url_for('campanha.upload_page'))

        if file and allowed_file(file.filename):
            try:
                column_map = {
                    'CÓDIGO DE BARRAS': 'codigo_barras', 'DESCRIÇÃO': 'descricao', 'PONTUAÇÃO': 'pontuacao',
                    'PREÇO NORMAL': 'preco_normal', 'PREÇO COM DESCONTO': 'preco_desconto',
                    'REBAIXE': 'rebaixe', 'QTD LIMITE': 'qtd_limite'
                }
                df = pd.read_excel(file).rename(columns=column_map)
                df = df.replace({np.nan: None})
                
                required_cols = column_map.values()
                if not all(col in df.columns for col in required_cols):
                    flash('A planilha não contém todas as colunas esperadas.', 'danger')
                    return redirect(url_for('campanha.upload_page'))

                produtos_para_inserir = [
                    (campanha_id, row.get('codigo_barras'), row.get('descricao'), row.get('pontuacao'),
                     row.get('preco_normal'), row.get('preco_desconto'), row.get('rebaixe'), row.get('qtd_limite'))
                    for _, row in df.iterrows()
                ]
                
                if produtos_para_inserir:
                    rowcount, error = db.add_products_bulk(produtos_para_inserir)
                    if error: flash(f'Erro ao salvar produtos: {error}', 'danger')
                    else: flash(f'{rowcount} produtos processados e salvos com sucesso!', 'success')
                else:
                    flash('Nenhum produto encontrado na planilha.', 'warning')
            except Exception as e:
                flash(f'Ocorreu um erro ao processar o arquivo: {e}', 'danger')
            return redirect(url_for('campanha.upload_page'))

    campanhas = db.get_active_campaigns_for_upload()
    return render_template('campanha/upload_campanha.html', active_page='upload', campanhas=campanhas)

@campanha_bp.route('/download_modelo')
def download_modelo():
    """
    Rota para baixar o arquivo .xlsx modelo para upload.
    """
    # O campanha_bp.root_path aponta para a pasta 'routes'
    # '..' sobe um nível para a raiz do projeto
    try:
        static_dir = os.path.join(campanha_bp.root_path, '..', 'static', 'models')
        filename = 'modelo_campanha.xlsx'
        return send_from_directory(
            static_dir,
            filename,
            as_attachment=True
        )
    except FileNotFoundError:
        flash('Arquivo modelo não encontrado no servidor.', 'danger')
        # Redireciona de volta para a página anterior ou uma página padrão
        return redirect(request.referrer or url_for('tabloide.gestao_tabloides'))

@campanha_bp.route('/gerenciar', methods=['GET', 'POST'])
def gestao_campanhas():
    if request.method == 'POST':
        nome = request.form.get('nome')
        data_inicio = request.form.get('data_inicio')
        data_fim = request.form.get('data_fim')
        if not all([nome, data_inicio, data_fim]):
            flash('Todos os campos são obrigatórios.', 'danger')
        else:
            error = db.add_campaign(nome, data_inicio, data_fim)
            if error: flash(f'Erro ao criar campanha: {error}', 'danger')
            else: flash('Campanha criada com sucesso!', 'success')
        return redirect(url_for('campanha.gestao_campanhas'))
    campanhas = db.get_all_campaigns()
    return render_template('campanha/campanhas.html', active_page='campanhas', campanhas=campanhas)

@campanha_bp.route('/editar/<int:campaign_id>', methods=['POST'])
def editar_campanha(campaign_id):
    nome = request.form.get('nome_edit')
    data_inicio = request.form.get('data_inicio_edit')
    data_fim = request.form.get('data_fim_edit')
    if not all([nome, data_inicio, data_fim]):
        flash('Todos os campos são obrigatórios para a edição.', 'danger')
    else:
        _, error = db.update_campaign(campaign_id, nome, data_inicio, data_fim)
        if error: flash(f'Erro ao atualizar campanha: {error}', 'danger')
        else: flash('Campanha atualizada com sucesso!', 'success')
    return redirect(url_for('campanha.gestao_campanhas'))

@campanha_bp.route('/deletar/<int:campaign_id>', methods=['POST'])
def deletar_campanha(campaign_id):
    _, error = db.delete_campaign(campaign_id)
    if error: flash(f'Erro ao desativar campanha: {error}', 'danger')
    else: flash('Campanha desativada com sucesso!', 'success')
    return redirect(url_for('campanha.gestao_campanhas'))

@campanha_bp.route('/<int:campanha_id>/produtos')
def produtos_por_campanha(campanha_id):
    campanha = db.get_campaign_by_id(campanha_id)
    if not campanha:
        flash('Campanha não encontrada.', 'danger')
        return redirect(url_for('campanha.gestao_campanhas'))
    produtos = db.get_products_by_campaign_id(campanha_id)
    return render_template('campanha/produtos_campanha.html', active_page='campanhas', campanha=campanha, produtos=produtos)

@campanha_bp.route('/<int:campanha_id>/produtos/adicionar', methods=['POST'])
def adicionar_produto(campanha_id):
    try:
        dados_produto = (
            campanha_id, request.form.get('codigo_barras'), request.form.get('descricao'),
            request.form.get('pontuacao') or None, request.form.get('preco_normal') or None,
            request.form.get('preco_desconto') or None, request.form.get('rebaixe') or None,
            request.form.get('qtd_limite') or None
        )
        _, error = db.add_single_product(dados_produto)
        if error: flash(f'Erro ao adicionar produto: {error}', 'danger')
        else: flash('Novo produto adicionado com sucesso!', 'success')
    except Exception as e:
        flash(f'Ocorreu um erro inesperado: {e}', 'danger')
    return redirect(url_for('campanha.produtos_por_campanha', campanha_id=campanha_id))

@campanha_bp.route('/<int:campanha_id>/produtos/atualizar', methods=['POST'])
def atualizar_produtos(campanha_id):
    selecionados = request.form.getlist('selecionado')
    if not selecionados:
        flash('Nenhum produto selecionado para atualizar.', 'warning')
        return redirect(url_for('campanha.produtos_por_campanha', campanha_id=campanha_id))
    produtos_para_atualizar = [
        (request.form.get(f'codigo_barras_{pid}'), request.form.get(f'descricao_{pid}'),
         request.form.get(f'pontuacao_{pid}') or None, request.form.get(f'preco_normal_{pid}') or None,
         request.form.get(f'preco_desconto_{pid}') or None, request.form.get(f'rebaixe_{pid}') or None,
         request.form.get(f'qtd_limite_{pid}') or None, pid)
        for pid in selecionados
    ]
    rowcount, error = db.update_products_in_bulk(produtos_para_atualizar)
    if error: flash(f'Erro ao atualizar produtos: {error}', 'danger')
    else: flash(f'{rowcount} produto(s) atualizado(s) com sucesso!', 'success')
    return redirect(url_for('campanha.produtos_por_campanha', campanha_id=campanha_id))

@campanha_bp.route('/<int:campanha_id>/produtos/deletar', methods=['POST'])
def deletar_produtos(campanha_id):
    selecionados = request.form.getlist('selecionado')
    if not selecionados:
        flash('Nenhum produto selecionado para deletar.', 'warning')
        return redirect(url_for('campanha.produtos_por_campanha', campanha_id=campanha_id))
    rowcount, error = db.delete_products_in_bulk(selecionados)
    if error: flash(f'Erro ao deletar produtos: {error}', 'danger')
    else: flash(f'{rowcount} produto(s) deletado(s) com sucesso!', 'success')
    return redirect(url_for('campanha.produtos_por_campanha', campanha_id=campanha_id))