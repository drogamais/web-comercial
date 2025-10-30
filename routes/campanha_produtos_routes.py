# routes/campanha_produtos_routes.py

import pandas as pd
import numpy as np
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, jsonify
)
import database.campanha_db as db_campanha
import database.campanha_produtos_db as db_campanha_produtos
import database.common_db as db_common
from utils import allowed_file, pad_barcode, clean_barcode
from config import DELETE_PASSWORD

campanha_produtos_bp = Blueprint(
    'campanha_produtos',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/campanha'
)

# --------------------------------------------------------

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
                # -----------------------------------------------------------
                # PASSO 1: DELETAR PRODUTOS EXISTENTES PARA ESTA CAMPANHA
                # -----------------------------------------------------------
                deleted_count, delete_error = db_campanha_produtos.delete_products_by_campaign_id(campanha_id)
                if delete_error:
                    flash(f'Erro ao limpar produtos antigos da campanha: {delete_error}', 'danger')
                    return redirect(url_for('campanha_produtos.upload_page'))
                if deleted_count > 0:
                    flash(f'{deleted_count} produto(s) antigo(s) removido(s) da campanha.', 'info')
                # -----------------------------------------------------------

                # PASSO 2: Ler e processar a nova planilha
                column_map = {
                    'CÓDIGO DE BARRAS': 'codigo_barras', 'DESCRIÇÃO': 'descricao', 'PONTUAÇÃO': 'pontuacao',
                    'PREÇO NORMAL': 'preco_normal', 'PREÇO COM DESCONTO': 'preco_desconto',
                    'REBAIXE': 'rebaixe', 'QTD LIMITE': 'qtd_limite'
                }
                df = pd.read_excel(file, dtype={'CÓDIGO DE BARRAS': str}).rename(columns=column_map)
                df = df.replace({np.nan: None})

                required_cols = list(column_map.values())
                if not all(col in df.columns for col in required_cols):
                    flash('A planilha não contém todas as colunas esperadas.', 'danger')
                    return redirect(url_for('campanha_produtos.upload_page'))

                # --- LÓGICA DE BUSCA DO CODIGO_INTERNO E NORMALIZAÇÃO ---
                gtins_raw_list = []
                gtins_normalizados_map = {}
                for g in df['codigo_barras'].tolist():
                    g_str = str(g) if g is not None else None
                    if g_str and g_str.strip():
                        gtins_raw_list.append(g_str)
                        normalized = pad_barcode(g_str)
                        if normalized:
                            gtins_normalizados_map[g_str] = normalized

                gtins_para_buscar = list(gtins_normalizados_map.values())

                if gtins_para_buscar:
                    ci_map_normalizado, err = db_common.get_codigo_interno_map_from_gtins(gtins_para_buscar)
                    if err:
                        flash(f'Erro ao buscar códigos internos: {err}', 'warning')
                        ci_map_normalizado = {}
                else:
                    ci_map_normalizado = {}
                # --- FIM DA LÓGICA ---

                produtos_para_inserir = []
                for _, row in df.iterrows():
                    cb_raw = row.get('codigo_barras')
                    cb_raw_str = str(cb_raw) if cb_raw is not None else None
                    cb_normalizado = pad_barcode(cb_raw_str)
                    ci = ci_map_normalizado.get(cb_normalizado) if cb_normalizado else None

                    produtos_para_inserir.append((
                        campanha_id,
                        cb_raw_str,
                        cb_normalizado,
                        ci,
                        row.get('descricao'),
                        row.get('pontuacao'),
                        row.get('preco_normal'),
                        row.get('preco_desconto'),
                        row.get('rebaixe'),
                        row.get('qtd_limite')
                    ))

                # PASSO 3: Inserir os novos produtos
                if produtos_para_inserir:
                    rowcount, error = db_campanha_produtos.add_products_bulk(produtos_para_inserir)
                    if error:
                        flash(f'Erro ao salvar novos produtos: {error}', 'danger')
                    else:
                        flash(f'{rowcount} novo(s) produto(s) processado(s) e salvo(s) com sucesso!', 'success')
                else:
                    flash('Nenhum produto encontrado na nova planilha para inserir.', 'warning')

            except Exception as e:
                flash(f'Ocorreu um erro ao processar o arquivo: {e}', 'danger')

            return redirect(url_for('campanha_produtos.upload_page'))

    # GET
    campanhas = db_campanha.get_all_campaigns()
    return render_template(
        'campanha/upload_campanha.html',
        active_page='campanha_upload',
        campanhas=campanhas
    )

@campanha_produtos_bp.route('/<int:campanha_id>/produtos')
def produtos_por_campanha(campanha_id):
    campanha = db_campanha.get_campaign_by_id(campanha_id)
    if not campanha:
        flash('Campanha não encontrada.', 'danger')
        return redirect(url_for('campanha.gestao_campanhas'))

    produtos = db_campanha_produtos.get_products_by_campaign_id(campanha_id)
    return render_template(
        'campanha/produtos_campanha.html', 
        active_page='campanhas_gestao', 
        campanha=campanha, 
        produtos=produtos
    )

@campanha_produtos_bp.route('/<int:campanha_id>/produtos/adicionar', methods=['POST'])
def adicionar_produto(campanha_id):
    try:
        cb_raw = request.form.get('codigo_barras')
        cb_normalizado = pad_barcode(cb_raw) # <-- NORMALIZA
        ci = None

        if cb_normalizado: # Busca CI com código normalizado
            ci_map_normalizado, err = db_common.get_codigo_interno_map_from_gtins([cb_normalizado])
            if err:
                flash(f'Aviso: Não foi possível buscar o Cód. Interno: {err}', 'warning')
            ci = ci_map_normalizado.get(cb_normalizado)

        # Adiciona cb_normalizado à tupla
        dados_produto = (
            campanha_id,
            cb_raw,
            cb_normalizado, # <-- CÓDIGO NORMALIZADO
            ci, # Código interno
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
    # Calcula normalizados para todos os selecionados
    gtins_normalizados_map = {pid: pad_barcode(gtins_raw_dict.get(pid)) for pid in selecionados}
    gtins_para_buscar = [norm for norm in gtins_normalizados_map.values() if norm] # Apenas normalizados válidos

    if gtins_para_buscar:
        # Busca CIs usando os códigos normalizados
        ci_map_normalizado, err = db_common.get_codigo_interno_map_from_gtins(gtins_para_buscar)
        if err:
            flash(f'Erro ao buscar códigos internos: {err}', 'warning')
            ci_map_normalizado = {}
    else:
        ci_map_normalizado = {}

    produtos_para_atualizar = []
    for pid in selecionados:
        cb_raw = gtins_raw_dict.get(pid)
        cb_normalizado = gtins_normalizados_map.get(pid) # Pega o normalizado já calculado
        # Busca o CI correspondente ao código normalizado
        ci = ci_map_normalizado.get(cb_normalizado) if cb_normalizado else None

        # Adiciona cb_normalizado à tupla para o UPDATE
        produtos_para_atualizar.append((
            cb_raw,
            cb_normalizado, # <-- CÓDIGO NORMALIZADO
            ci, # Código interno
            request.form.get(f'descricao_{pid}'),
            request.form.get(f'pontuacao_{pid}') or None,
            request.form.get(f'preco_normal_{pid}') or None,
            request.form.get(f'preco_desconto_{pid}') or None,
            request.form.get(f'rebaixe_{pid}') or None,
            request.form.get(f'qtd_limite_{pid}') or None,
            pid # ID do produto no final para o WHERE
        ))

    rowcount, error = db_campanha_produtos.update_products_in_bulk(produtos_para_atualizar)
    if error: flash(f'Erro ao atualizar produtos: {error}', 'danger')
    else: flash(f'{rowcount} produto(s) atualizado(s) com sucesso!', 'success')
    return redirect(url_for('campanha_produtos.produtos_por_campanha', campanha_id=campanha_id))

@campanha_produtos_bp.route('/<int:campanha_id>/produtos/deletar', methods=['POST'])
def deletar_produtos(campanha_id):
    # --- NOVO: Verificação de Senha para Deleção em Massa ---
    confirmation_password = request.form.get('confirmation_password_bulk')
    if confirmation_password != DELETE_PASSWORD:
        flash('Senha de confirmação incorreta para deleção em massa.', 'danger')
        return redirect(url_for('campanha_produtos.produtos_por_campanha', campanha_id=campanha_id))
    # --- FIM NOVO ---
    
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

    # 1. USANDO clean_barcode para limpar e obter o GTIN sem padding
    gtins_para_validar_raw = [clean_barcode(gtin) for gtin in gtins_raw if gtin and str(gtin).strip()]
    gtins_para_validar_raw = [g for g in gtins_para_validar_raw if g]

    if not gtins_para_validar_raw:
         return jsonify({"valid_gtins": []})

    # 2. Envia os GTINs RAW (sem padding) para a função de banco
    validos_raw_set, error = db_common.validate_gtins_in_external_db(gtins_para_validar_raw)

    if error:
        return jsonify({"error": error}), 500

    # 3. Retorna o set de GTINs válidos (que já estão no formato raw/cleaned)
    return jsonify({"valid_gtins": list(validos_raw_set)})