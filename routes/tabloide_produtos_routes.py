# routes/tabloide_produtos_routes.py

import pandas as pd
import numpy as np
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
)
import database.tabloide_db as db_tabloide
import database.tabloide_produtos_db as db_tabloide_produtos
import database.common_db as db_common
from utils import allowed_file, pad_barcode, clean_barcode, DELETE_PASSWORD
import io # <-- ADICIONAR IMPORT

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
            # --- MUDANÇA HTMX ---
            # REMOVIDO: return redirect(url_for('tabloide_produtos.upload_page'))
        
        file = request.files.get('file')
        if not file or file.filename == '':
            flash('Nenhum arquivo selecionado.', 'danger')
            # --- MUDANÇA HTMX ---
            # REMOVIDO: return redirect(url_for('tabloide_produtos.upload_page'))

        elif file and allowed_file(file.filename):
            try:
                # ---------------------------------------------------------
                # PASSO 1: DELETAR PRODUTOS EXISTENTES PARA ESTE TABLOIDE
                # ---------------------------------------------------------
                deleted_count, delete_error = db_tabloide_produtos.delete_products_by_tabloide_id(tabloide_id)
                if delete_error:
                    flash(f'Erro ao limpar produtos antigos do tabloide: {delete_error}', 'danger')
                    # --- MUDANÇA HTMX ---
                    # REMOVIDO: return redirect(url_for('tabloide_produtos.upload_page'))
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
                    # --- MUDANÇA HTMX ---
                    # REMOVIDO: return redirect(url_for('tabloide_produtos.upload_page'))
                    
                    # Adicionado para evitar erro de variável indefinida
                    tabloides = db_tabloide.get_all_tabloide()
                    return render_template(
                        'tabloide/upload_tabloide.html',
                        active_page='tabloide_upload',
                        tabloides=tabloides
                    )


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
                    # --- MUDANÇA HTMX ---
                    # REMOVIDO: return redirect(url_for('tabloide_produtos.upload_page'))
                
                else:
                    df = df.rename(columns=column_map)
                    df = df.replace({np.nan: None})

                    cols_to_numeric = ['preco_normal', 'preco_desconto', 'preco_desconto_cliente', 'preco_app']
                    for col in cols_to_numeric:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce').replace({np.nan: None})

                    # --- LÓGICA DE BUSCA DO CODIGO_INTERNO E NORMALIZAÇÃO ---
                    gtins_raw_list = []
                    gtins_para_buscar_map = {} # Mapeia para garantir apenas códigos RAW únicos
                    
                    for g in df['codigo_barras'].tolist():
                        g_str = str(g) if g is not None else None
                        if g_str and g_str.strip():
                            gtins_raw_list.append(g_str)
                            cleaned = clean_barcode(g_str) # <-- AGORA USA CLEAN_BARCODE
                            if cleaned:
                                gtins_para_buscar_map[cleaned] = cleaned 

                    gtins_para_buscar_raw = list(gtins_para_buscar_map.keys()) # Lista de GTINs RAW únicos para buscar

                    if gtins_para_buscar_raw:
                        # FIX: Passa a lista RAW para o common_db
                        ci_map_raw, err = db_common.get_codigo_interno_map_from_gtins(gtins_para_buscar_raw)
                        if err:
                            flash(f'Erro ao buscar códigos internos: {err}', 'warning')
                            ci_map_raw = {}
                    else:
                        ci_map_raw = {}
                    # --- FIM DA LÓGICA ---

                    produtos_para_inserir = []
                    for _, row in df.iterrows():
                        cb_raw = row.get('codigo_barras')
                        cb_raw_str = str(cb_raw) if cb_raw is not None else None
                        cb_normalizado = pad_barcode(cb_raw_str)
                        
                        # FIX: Usa o GTIN LIMPO como chave para buscar o CI
                        cb_cleaned = clean_barcode(cb_raw_str) 
                        ci = ci_map_raw.get(cb_cleaned) if cb_cleaned else None

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

            # --- MUDANÇA HTMX ---
            # REMOVIDO: return redirect(url_for('tabloide_produtos.upload_page'))

    # GET (ou continuação do POST)
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
        cb_normalizado = pad_barcode(cb_raw) # <-- NORMALIZA (para salvar)
        cb_cleaned = clean_barcode(cb_raw) # <-- GTIN LIMPO (para buscar CI)
        ci = None

        if cb_cleaned: # Busca CI com código limpo
            ci_map_raw, err = db_common.get_codigo_interno_map_from_gtins([cb_cleaned])
            if err:
                flash(f'Aviso: Não foi possível buscar o Cód. Interno: {err}', 'warning')
            ci = ci_map_raw.get(cb_cleaned)

        # Adiciona cb_normalizado à tupla
        dados_produto = (
            tabloide_id,
            cb_raw,
            cb_normalizado, # <-- CÓDIGO NORMALIZADO (salva no DB)
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

    # --- MUDANÇA HTMX ---
    tabloide = db_tabloide.get_tabloide_by_id(tabloide_id)
    produtos = db_tabloide_produtos.get_products_by_tabloide_id(tabloide_id)
    return render_template(
        'tabloide/produtos_tabloide.html', 
        active_page='tabloides_gestao', 
        tabloide=tabloide, 
        produtos=produtos
    )


@tabloide_produtos_bp.route('/<int:tabloide_id>/produtos/atualizar', methods=['POST'])
def atualizar_produtos(tabloide_id):
    selecionados = request.form.getlist('selecionado')
    if not selecionados:
        flash('Nenhum produto selecionado para atualizar.', 'warning')
    else:
        gtins_raw_dict = {pid: request.form.get(f'codigo_barras_{pid}') for pid in selecionados}
        # FIX: Calcula GTINs RAW para pesquisa
        gtins_cleaned_map = {pid: clean_barcode(gtins_raw_dict.get(pid)) for pid in selecionados}
        gtins_para_buscar_raw = [cleaned for cleaned in gtins_cleaned_map.values() if cleaned] # Apenas RAW válidos

        if gtins_para_buscar_raw:
            # Busca CIs usando os códigos RAW
            ci_map_raw, err = db_common.get_codigo_interno_map_from_gtins(gtins_para_buscar_raw)
            if err:
                flash(f'Erro ao buscar códigos internos: {err}', 'warning')
                ci_map_raw = {}
        else:
            ci_map_raw = {}

        produtos_para_atualizar = []
        for pid in selecionados:
            cb_raw = gtins_raw_dict.get(pid)
            cb_normalizado = pad_barcode(cb_raw) # Recalcula o normalizado (para salvar)
            
            # FIX: Pega o RAW GTIN para lookup
            cb_cleaned = gtins_cleaned_map.get(pid) 
            
            # FIX: Busca o CI correspondente ao código RAW
            ci = ci_map_raw.get(cb_cleaned) if cb_cleaned else None

            # Adiciona cb_normalizado à tupla para o UPDATE
            produtos_para_atualizar.append((
                cb_raw,
                cb_normalizado, # <-- CÓDIGO NORMALIZADO (salva no DB)
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
            
    # --- MUDANÇA HTMX ---
    tabloide = db_tabloide.get_tabloide_by_id(tabloide_id)
    produtos = db_tabloide_produtos.get_products_by_tabloide_id(tabloide_id)
    return render_template(
        'tabloide/produtos_tabloide.html', 
        active_page='tabloides_gestao', 
        tabloide=tabloide, 
        produtos=produtos
    )


@tabloide_produtos_bp.route('/<int:tabloide_id>/produtos/deletar', methods=['POST'])
def deletar_produtos(tabloide_id):
    # --- NOVO: Verificação de Senha para Deleção em Massa ---
    confirmation_password = request.form.get('confirmation_password_bulk')
    if confirmation_password != DELETE_PASSWORD:
        flash('Senha de confirmação incorreta para deleção em massa.', 'danger')
    else:
        selecionados = request.form.getlist('selecionado')
        if not selecionados:
            flash('Nenhum produto selecionado para deletar.', 'warning')
        else:
            rowcount, error = db_tabloide_produtos.delete_products_in_bulk(selecionados)
            if error:
                flash(f'Erro ao deletar produtos: {error}', 'danger')
            else:
                flash(f'{rowcount} produto(s) deletado(s) com sucesso!', 'success')
                
    # --- MUDANÇA HTMX ---
    tabloide = db_tabloide.get_tabloide_by_id(tabloide_id)
    produtos = db_tabloide_produtos.get_products_by_tabloide_id(tabloide_id)
    return render_template(
        'tabloide/produtos_tabloide.html', 
        active_page='tabloides_gestao', 
        tabloide=tabloide, 
        produtos=produtos
    )

@tabloide_produtos_bp.route('/<int:tabloide_id>/produtos/validar_gtins', methods=['POST'])
def validar_gtins_tabloide(tabloide_id):
    data = request.get_json()
    products_data = data.get('products', []) # Espera [{id: '1', gtin: '123'}]

    if not products_data:
        return jsonify({"error": "Nenhum produto enviado"}), 400

    # 1. Extrai GTINs para validação e busca de CI
    gtins_map = {p['id']: clean_barcode(p['gtin']) for p in products_data if p.get('gtin') and p.get('id')}
    gtins_para_buscar = list(set(gtins_map.values())) # Lista única de GTINs limpos

    if not gtins_para_buscar:
        return jsonify({"valid_gtins": [], "updated_count": 0})

    # 2. Valida quais GTINs existem (para colorir a UI)
    validos_raw_set, error_val = db_common.validate_gtins_in_external_db(gtins_para_buscar)
    if error_val:
        return jsonify({"error": f"Erro ao validar GTINs: {error_val}"}), 500

    # 3. Busca os Códigos Internos (CI) para os GTINs (apenas os principais)
    ci_map_raw, error_ci = db_common.get_codigo_interno_map_from_gtins(gtins_para_buscar)
    if error_ci:
        return jsonify({"error": f"Erro ao buscar CIs: {error_ci}"}), 500

    # 4. Prepara a lista para o update no banco
    produtos_para_atualizar = []
    for product_id, gtin_limpo in gtins_map.items():
        if gtin_limpo in ci_map_raw: # Só atualiza se achou um CI principal
            cb_normalizado = pad_barcode(gtin_limpo)
            ci = ci_map_raw.get(gtin_limpo)
            # Tupla: (cb, cbn, ci, id)
            produtos_para_atualizar.append((
                gtin_limpo,       # codigo_barras
                cb_normalizado, # codigo_barras_normalizado
                ci,             # codigo_interno
                product_id      # id
            ))

    # 5. Executa o Update no banco
    updated_count = 0
    if produtos_para_atualizar:
        # !! IMPORTANTE: Chamar a função correta do DB (tabloide) !!
        rowcount, error_update = db_tabloide_produtos.update_product_ci_bulk(produtos_para_atualizar)
        if error_update:
            print(f"Erro ao atualizar CIs em tabloide_produtos_db: {error_update}")
        else:
            updated_count = rowcount

    # 6. Retorna a lista de GTINs válidos (para UI) e a contagem de updates
    return jsonify({
        "valid_gtins": list(validos_raw_set),
        "updated_count": updated_count
    })


@tabloide_produtos_bp.route('/<int:tabloide_id>/exportar')
def exportar_produtos(tabloide_id):
    try:
        # 1. Buscar nome
        tabloide = db_tabloide.get_tabloide_by_id(tabloide_id)
        tabloide_nome = tabloide.nome if tabloide else f"tabloide_{tabloide_id}"
        
        # 2. Buscar dados
        produtos_data = db_tabloide_produtos.get_products_by_tabloide_id(tabloide_id)
        if not produtos_data:
            flash('Nenhum produto encontrado para exportar.', 'warning')
            return redirect(url_for('tabloide_produtos.produtos_por_tabloide', tabloide_id=tabloide_id))
        
        # 3. DataFrame
        produtos_list = [dict(row) for row in produtos_data]
        df = pd.DataFrame(produtos_list)

        # 4. Colunas (INCLUINDO CODIGO_INTERNO)
        colunas_exportar = {
            "codigo_interno": "Codigo Interno",
            "codigo_barras": "GTIN",
            "descricao": "DESCRIÇÃO",
            "laboratorio": "LABORATÓRIO",
            "tipo_preco": "TIPO DE PREÇO",
            "preco_normal": "PREÇO NORMAL",
            "preco_desconto": "PRECO DESCONTO GERAL",
            "preco_desconto_cliente": "PREÇO DESCONTO CLIENTE+",
            "tipo_regra": "TIPO REGRA",
            "preco_app": "PREÇO APP"
        }
        
        # Filtra o DF para ter apenas as colunas que existem no DF e queremos
        colunas_presentes = [col for col in colunas_exportar.keys() if col in df.columns]
        df_final = df[colunas_presentes].rename(columns=colunas_exportar)


        # 5. Criar arquivo em memória
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Produtos Tabloide')
        output.seek(0)
        
        # 6. Enviar arquivo
        return send_file(
            output,
            as_attachment=True,
            download_name=f"export_produtos_tabloide_{tabloide_nome}.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        flash(f'Ocorreu um erro ao gerar o arquivo Excel: {e}', 'danger')
        return redirect(url_for('tabloide_produtos.produtos_por_tabloide', tabloide_id=tabloide_id))