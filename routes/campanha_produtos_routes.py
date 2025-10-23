# routes/campanha_produtos_routes.py

import pandas as pd
import numpy as np
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, jsonify
)
import database.campanha_db as db_campanha # Para listar campanhas no upload
import database.campanha_produtos_db as db_campanha_produtos # Para gerenciar produtos
import database.common_db as db_common # Para validar GTIN e Cód. Interno
from utils import allowed_file

# Cria o Blueprint de Produtos de Campanha
campanha_produtos_bp = Blueprint(
    'campanha_produtos',  # Nome do blueprint (usado em url_for)
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/campanha' # Mesmo prefixo do pai
)

@campanha_produtos_bp.route('/upload', methods=['GET', 'POST'])
def upload_page():
    if request.method == 'POST':
        campanha_id = request.form.get('campanha')
        if not campanha_id:
            flash('Por favor, selecione uma campanha.', 'danger')
            return redirect(url_for('campanha_produtos.upload_page'))

        file = request.files.get('file')
        if not file or file.filename == '':
            flash('Nenhum arquivo selecionado.', 'danger')
            return redirect(url_for('campanha_produtos.upload_page'))

        if file and allowed_file(file.filename):
            try:
                column_map = {
                    'CÓDIGO DE BARRAS': 'codigo_barras', 'DESCRIÇÃO': 'descricao', 'PONTUAÇÃO': 'pontuacao',
                    'PREÇO NORMAL': 'preco_normal', 'PREÇO COM DESCONTO': 'preco_desconto',
                    'REBAIXE': 'rebaixe', 'QTD LIMITE': 'qtd_limite'
                }
                df = pd.read_excel(file, dtype={'CÓDIGO DE BARRAS': str}).rename(columns=column_map)
                df = df.replace({np.nan: None})
                
                required_cols = column_map.values()
                if not all(col in df.columns for col in required_cols):
                    flash('A planilha não contém todas as colunas esperadas.', 'danger')
                    return redirect(url_for('campanha_produtos.upload_page'))

                # --- LÓGICA DE BUSCA DO CODIGO_INTERNO ---
                gtins_raw = [g for g in df['codigo_barras'].tolist() if g and g.strip()]
                if gtins_raw:
                    gtins_padded = [g.zfill(14) for g in gtins_raw]
                    map_padded_to_raw = {padded: raw for padded, raw in zip(gtins_padded, gtins_raw)}
                    ci_map_padded, err = db_common.get_codigo_interno_map_from_gtins(gtins_padded)
                    if err:
                        flash(f'Erro ao buscar códigos internos: {err}', 'warning')
                        ci_map_padded = {}
                    ci_map_raw = {map_padded_to_raw[p]: ci for p, ci in ci_map_padded.items() if p in map_padded_to_raw}
                else:
                    ci_map_raw = {}
                # --- FIM DA LÓGICA ---

                produtos_para_inserir = []
                for _, row in df.iterrows():
                    cb_raw = row.get('codigo_barras')
                    ci = ci_map_raw.get(cb_raw) 
                    
                    produtos_para_inserir.append((
                        campanha_id, 
                        cb_raw, 
                        ci, # Coluna nova
                        row.get('descricao'), 
                        row.get('pontuacao'),
                        row.get('preco_normal'), 
                        row.get('preco_desconto'), 
                        row.get('rebaixe'), 
                        row.get('qtd_limite')
                    ))
                
                if produtos_para_inserir:
                    rowcount, error = db_campanha_produtos.add_products_bulk(produtos_para_inserir)
                    if error: flash(f'Erro ao salvar produtos: {error}', 'danger')
                    else: flash(f'{rowcount} produtos processados e salvos com sucesso!', 'success')
                else:
                    flash('Nenhum produto encontrado na planilha.', 'warning')
            except Exception as e:
                flash(f'Ocorreu um erro ao processar o arquivo: {e}', 'danger')
            return redirect(url_for('campanha_produtos.upload_page'))

    # GET
    campanhas = db_campanha.get_active_campaigns_for_upload()
    return render_template('campanha/upload_campanha.html', active_page='upload', campanhas=campanhas)


@campanha_produtos_bp.route('/<int:campanha_id>/produtos')
def produtos_por_campanha(campanha_id):
    campanha = db_campanha.get_campaign_by_id(campanha_id)
    if not campanha:
        flash('Campanha não encontrada.', 'danger')
        return redirect(url_for('campanha.gestao_campanhas'))
    
    produtos = db_campanha_produtos.get_products_by_campaign_id(campanha_id)
    return render_template('campanha/produtos_campanha.html', active_page='campanhas', campanha=campanha, produtos=produtos)

@campanha_produtos_bp.route('/<int:campanha_id>/produtos/adicionar', methods=['POST'])
def adicionar_produto(campanha_id):
    try:
        cb_raw = request.form.get('codigo_barras')
        ci = None

        if cb_raw and cb_raw.strip():
            cb_padded = cb_raw.strip().zfill(14)
            ci_map_padded, err = db_common.get_codigo_interno_map_from_gtins([cb_padded])
            if err:
                flash(f'Aviso: Não foi possível buscar o Cód. Interno: {err}', 'warning')
            ci = ci_map_padded.get(cb_padded)

        dados_produto = (
            campanha_id, 
            cb_raw, 
            ci, # Coluna nova
            request.form.get('descricao'),
            request.form.get('pontuacao') or None, 
            request.form.get('preco_normal') or None,
            request.form.get('preco_desconto') or None, 
            request.form.get('rebaixe') or None,
            request.form.get('qtd_limite') or None
        )
        _, error = db_campanha_produtos.add_single_product(dados_produto)
        if error: flash(f'Erro ao adicionar produto: {error}', 'danger')
        else: flash('Novo produto adicionado com sucesso!', 'success')
    except Exception as e:
        flash(f'Ocorreu um erro inesperado: {e}', 'danger')
    return redirect(url_for('campanha_produtos.produtos_por_campanha', campanha_id=campanha_id))

@campanha_produtos_bp.route('/<int:campanha_id>/produtos/atualizar', methods=['POST'])
def atualizar_produtos(campanha_id):
    selecionados = request.form.getlist('selecionado')
    if not selecionados:
        flash('Nenhum produto selecionado para atualizar.', 'warning')
        return redirect(url_for('campanha_produtos.produtos_por_campanha', campanha_id=campanha_id))
    
    gtins_raw_dict = {pid: request.form.get(f'codigo_barras_{pid}') for pid in selecionados}
    gtins_raw_list = [g for g in gtins_raw_dict.values() if g and g.strip()]
    
    if gtins_raw_list:
        gtins_padded = [g.zfill(14) for g in gtins_raw_list]
        map_padded_to_raw = {padded: raw for padded, raw in zip(gtins_padded, gtins_raw_list)}
        ci_map_padded, err = db_common.get_codigo_interno_map_from_gtins(gtins_padded)
        if err:
            flash(f'Erro ao buscar códigos internos: {err}', 'warning')
            ci_map_padded = {}
        ci_map_raw = {map_padded_to_raw[p]: ci for p, ci in ci_map_padded.items() if p in map_padded_to_raw}
    else:
        ci_map_raw = {}

    produtos_para_atualizar = []
    for pid in selecionados:
        cb_raw = gtins_raw_dict.get(pid)
        ci = ci_map_raw.get(cb_raw)
        
        if ci is None:
             if not cb_raw or not cb_raw.strip():
                 ci = None
             
        produtos_para_atualizar.append((
            cb_raw, 
            ci, # Coluna nova
            request.form.get(f'descricao_{pid}'),
            request.form.get(f'pontuacao_{pid}') or None, 
            request.form.get(f'preco_normal_{pid}') or None,
            request.form.get(f'preco_desconto_{pid}') or None, 
            request.form.get(f'rebaixe_{pid}') or None,
            request.form.get(f'qtd_limite_{pid}') or None, 
            pid
        ))

    rowcount, error = db_campanha_produtos.update_products_in_bulk(produtos_para_atualizar)
    if error: flash(f'Erro ao atualizar produtos: {error}', 'danger')
    else: flash(f'{rowcount} produto(s) atualizado(s) com sucesso!', 'success')
    return redirect(url_for('campanha_produtos.produtos_por_campanha', campanha_id=campanha_id))

@campanha_produtos_bp.route('/<int:campanha_id>/produtos/deletar', methods=['POST'])
def deletar_produtos(campanha_id):
    selecionados = request.form.getlist('selecionado')
    if not selecionados:
        flash('Nenhum produto selecionado para deletar.', 'warning')
        return redirect(url_for('campanha_produtos.produtos_por_campanha', campanha_id=campanha_id))
    
    rowcount, error = db_campanha_produtos.delete_products_in_bulk(selecionados)
    if error: flash(f'Erro ao deletar produtos: {error}', 'danger')
    else: flash(f'{rowcount} produto(s) deletado(s) com sucesso!', 'success')
    return redirect(url_for('campanha_produtos.produtos_por_campanha', campanha_id=campanha_id))

@campanha_produtos_bp.route('/<int:campanha_id>/produtos/validar_gtins', methods=['POST'])
def validar_gtins(campanha_id):
    data = request.get_json()
    gtins_raw = data.get('gtins', [])

    if not gtins_raw:
        return jsonify({"error": "Nenhum GTIN enviado"}), 400

    gtins_para_validar_raw = [gtin for gtin in gtins_raw if gtin and gtin.strip()]
    
    if not gtins_para_validar_raw:
        return jsonify({"valid_gtins": []})

    gtins_padded = [g.zfill(14) for g in gtins_para_validar_raw] 
    map_padded_to_raw = {padded: raw for padded, raw in zip(gtins_padded, gtins_para_validar_raw)}

    validos_padded, error = db_common.validate_gtins_in_external_db(gtins_padded)
    
    if error:
        return jsonify({"error": error}), 500
    
    validos_raw = {map_padded_to_raw[padded_gtin] for padded_gtin in validos_padded if padded_gtin in map_padded_to_raw}

    return jsonify({"valid_gtins": list(validos_raw)})