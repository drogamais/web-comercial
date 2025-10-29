# routes/tabloide_produtos_routes.py

import pandas as pd
import numpy as np
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, jsonify
)
import database.tabloide_db as db_tabloide
import database.tabloide_produtos_db as db_tabloide_produtos
import database.common_db as db_common
from utils import allowed_file, pad_barcode, clean_barcode

tabloide_produtos_bp = Blueprint(
    'tabloide_produtos',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/tabloide'
)

# --------------------------------------------------------


@tabloide_produtos_bp.route('/upload', methods=['GET', 'POST'])
def upload_page():
    if request.method == 'POST':
        tabloide_id = request.form.get('tabloide')
        if not tabloide_id:
            flash('Por favor, selecione um tabloide.', 'danger')
            return redirect(url_for('tabloide_produtos.upload_page'))

        file = request.files.get('file')
        if not file or file.filename == '':
            flash('Nenhum arquivo selecionado.', 'danger')
            return redirect(url_for('tabloide_produtos.upload_page'))

        if file and allowed_file(file.filename):
            try:
                # ---------------------------------------------------------
                # PASSO 1: DELETAR PRODUTOS EXISTENTES PARA ESTE TABLOIDE
                # ---------------------------------------------------------
                deleted_count, delete_error = db_tabloide_produtos.delete_products_by_tabloide_id(tabloide_id)
                if delete_error:
                    flash(f'Erro ao limpar produtos antigos do tabloide: {delete_error}', 'danger')
                    return redirect(url_for('tabloide_produtos.upload_page'))
                if deleted_count > 0:
                    flash(f'{deleted_count} produto(s) antigo(s) removido(s) do tabloide.', 'info')
                # ---------------------------------------------------------

                # PASSO 2: Ler e processar a nova planilha
                column_map = {
                    'GTIN': 'codigo_barras', 'DESCRIÇÃO': 'descricao', 'LABORATÓRIO': 'laboratorio',
                    'TIPO DE PREÇO': 'tipo_preco', 'PREÇO NORMAL': 'preco_normal',
                    'PREÇO DESCONTO GERAL': 'preco_desconto', 'PREÇO DESCONTO CLIENTE+': 'preco_desconto_cliente',
                    'PREÇO APP': 'preco_app', 'TIPO DE REGRA': 'tipo_regra'
                }

                try:
                    df = pd.read_excel(file, sheet_name='Todos', dtype={'GTIN': str})
                except Exception as e:
                    flash(f'Erro ao ler a planilha. Verifique se a aba "Todos" existe e se a coluna GTIN está presente. (Erro: {e})', 'danger')
                    return redirect(url_for('tabloide_produtos.upload_page'))

                df.columns = (
                    df.columns.astype(str)
                    .str.replace(r'\s+', ' ', regex=True)
                    .str.replace(r'\s\+', '+', regex=True)
                    .str.strip()
                    .str.upper()
                )

                required_source_cols = list(column_map.keys())
                missing_cols = [col for col in required_source_cols if col not in df.columns]
                if missing_cols:
                    flash(f'A planilha (aba "Todos") não contém todas as colunas esperadas. Faltando: {", ".join(missing_cols)}', 'danger')
                    return redirect(url_for('tabloide_produtos.upload_page'))

                df = df.rename(columns=column_map)
                df = df.replace({np.nan: None})

                cols_to_numeric = ['preco_normal', 'preco_desconto', 'preco_desconto_cliente', 'preco_app']
                for col in cols_to_numeric:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce').replace({np.nan: None})

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
                        tabloide_id,
                        cb_raw_str,
                        cb_normalizado,
                        ci,
                        row.get('descricao'),
                        row.get('laboratorio'),
                        row.get('tipo_preco'),
                        row.get('preco_normal'),
                        row.get('preco_desconto'),
                        row.get('preco_desconto_cliente'),
                        row.get('preco_app'),
                        row.get('tipo_regra')
                    ))

                # PASSO 3: Inserir os novos produtos
                if produtos_para_inserir:
                    rowcount, error = db_tabloide_produtos.add_products_bulk(produtos_para_inserir)
                    if error:
                        flash(f'Erro ao salvar novos produtos: {error}', 'danger')
                    else:
                        flash(f'{rowcount} novo(s) produto(s) processado(s) e salvo(s) com sucesso!', 'success')
                else:
                    flash('Nenhum produto encontrado na nova planilha para inserir.', 'warning')

            except Exception as e:
                flash(f'Ocorreu um erro inesperado ao processar o arquivo: {e}', 'danger')

            return redirect(url_for('tabloide_produtos.upload_page'))

    # GET
    tabloides = db_tabloide.get_all_tabloide()
    return render_template(
        'tabloide/upload_tabloide.html',
        active_page='tabloide_upload',
        tabloides=tabloides
    )


@tabloide_produtos_bp.route('/<int:tabloide_id>/produtos')
def produtos_por_tabloide(tabloide_id):
    tabloide = db_tabloide.get_tabloide_by_id(tabloide_id)
    if not tabloide:
        flash('Tabloide não encontrado.', 'danger')
        return redirect(url_for('tabloide.gestao_tabloides'))

    produtos = db_tabloide_produtos.get_products_by_tabloide_id(tabloide_id)
    return render_template(
        'tabloide/produtos_tabloide.html', 
        active_page='tabloides_gestao', 
        tabloide=tabloide, 
        produtos=produtos
    )


@tabloide_produtos_bp.route('/<int:tabloide_id>/produtos/adicionar', methods=['POST'])
def adicionar_produto(tabloide_id):
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
            tabloide_id,
            cb_raw,
            cb_normalizado, # <-- CÓDIGO NORMALIZADO
            ci, # Código interno
            request.form.get('descricao'),
            request.form.get('laboratorio') or None,
            request.form.get('tipo_preco') or None,
            request.form.get('preco_normal') or None,
            request.form.get('preco_desconto') or None,
            request.form.get('preco_desconto_cliente') or None,
            request.form.get('preco_app') or None,
            request.form.get('tipo_regra') or None
        )
        _, error = db_tabloide_produtos.add_single_product(dados_produto)
        if error:
            flash(f'Erro ao adicionar produto: {error}', 'danger')
        else:
            flash('Novo produto adicionado com sucesso!', 'success')
    except Exception as e:
        flash(f'Ocorreu um erro inesperado: {e}', 'danger')
    return redirect(url_for('tabloide_produtos.produtos_por_tabloide', tabloide_id=tabloide_id))


@tabloide_produtos_bp.route('/<int:tabloide_id>/produtos/atualizar', methods=['POST'])
def atualizar_produtos(tabloide_id):
    selecionados = request.form.getlist('selecionado')
    if not selecionados:
        flash('Nenhum produto selecionado para atualizar.', 'warning')
        return redirect(url_for('tabloide_produtos.produtos_por_tabloide', tabloide_id=tabloide_id))

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
            request.form.get(f'laboratorio_{pid}') or None,
            request.form.get(f'tipo_preco_{pid}') or None,
            request.form.get(f'preco_normal_{pid}') or None,
            request.form.get(f'preco_desconto_{pid}') or None,
            request.form.get(f'preco_desconto_cliente_{pid}') or None,
            request.form.get(f'preco_app_{pid}') or None,
            request.form.get(f'tipo_regra_{pid}') or None,
            pid # ID do produto no final para o WHERE
        ))

    rowcount, error = db_tabloide_produtos.update_products_in_bulk(produtos_para_atualizar)
    if error:
        flash(f'Erro ao atualizar produtos: {error}', 'danger')
    else:
        flash(f'{rowcount} produto(s) atualizado(s) com sucesso!', 'success')
    return redirect(url_for('tabloide_produtos.produtos_por_tabloide', tabloide_id=tabloide_id))


@tabloide_produtos_bp.route('/<int:tabloide_id>/produtos/deletar', methods=['POST'])
def deletar_produtos(tabloide_id):
    selecionados = request.form.getlist('selecionado')
    if not selecionados:
        flash('Nenhum produto selecionado para deletar.', 'warning')
        return redirect(url_for('tabloide_produtos.produtos_por_tabloide', tabloide_id=tabloide_id))

    rowcount, error = db_tabloide_produtos.delete_products_in_bulk(selecionados)
    if error:
        flash(f'Erro ao deletar produtos: {error}', 'danger')
    else:
        flash(f'{rowcount} produto(s) deletado(s) com sucesso!', 'success')
    return redirect(url_for('tabloide_produtos.produtos_por_tabloide', tabloide_id=tabloide_id))

@tabloide_produtos_bp.route('/<int:tabloide_id>/produtos/validar_gtins', methods=['POST'])
def validar_gtins_tabloide(tabloide_id):
    data = request.get_json()
    gtins_raw = data.get('gtins', [])

    if not gtins_raw:
        return jsonify({"error": "Nenhum GTIN enviado"}), 400

    # 1. USANDO clean_barcode
    gtins_para_validar_raw = [clean_barcode(gtin) for gtin in gtins_raw if gtin and str(gtin).strip()]
    gtins_para_validar_raw = [g for g in gtins_para_validar_raw if g]

    if not gtins_para_validar_raw:
         return jsonify({"valid_gtins": []})

    # 2. Envia os GTINs RAW (sem padding) para a função de banco
    validos_raw_set, error = db_common.validate_gtins_in_external_db(gtins_para_validar_raw)

    if error:
        error_message = f"Erro ao validar GTINs no banco externo: {error}"
        print(f"Erro na rota validar_gtins_tabloide: {error_message}")
        return jsonify({"error": error_message}), 500

    # 3. Retorna o set de GTINs válidos (que já estão no formato raw/cleaned)
    return jsonify({"valid_gtins": list(validos_raw_set)})