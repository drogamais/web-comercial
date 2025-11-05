# routes/campanha_produtos_routes.py

import pandas as pd
import numpy as np
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
)
import database.campanha_db as db_campanha
import database.campanha_produtos_db as db_campanha_produtos
import database.common_db as db_common
from utils import allowed_file, pad_barcode, clean_barcode, DELETE_PASSWORD
import io # <-- ADICIONAR IMPORT

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
            # --- MUDANÇA HTMX ---
            # Não redireciona, renderiza a página de upload novamente
            # O flash message será exibido
            # REMOVIDO: return redirect(url_for('campanha_produtos.upload_page'))

        file = request.files.get('file')
        if not file or file.filename == '':
            flash('Nenhum arquivo selecionado.', 'danger')
            # --- MUDANÇA HTMX ---
            # REMOVIDO: return redirect(url_for('campanha_produtos.upload_page'))

        elif file and allowed_file(file.filename):
            try:
                # -----------------------------------------------------------
                # PASSO 1: DELETAR PRODUTOS EXISTENTES PARA ESTA CAMPANHA
                # -----------------------------------------------------------
                deleted_count, delete_error = db_campanha_produtos.delete_products_by_campaign_id(campanha_id)
                if delete_error:
                    flash(f'Erro ao limpar produtos antigos da campanha: {delete_error}', 'danger')
                    # --- MUDANÇA HTMX ---
                    # REMOVIDO: return redirect(url_for('campanha_produtos.upload_page'))
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
                    # --- MUDANÇA HTMX ---
                    # REMOVIDO: return redirect(url_for('campanha_produtos.upload_page'))
                
                else:
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

    # GET (ou continuação do POST)
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
            campanha_id,
            cb_raw,
            cb_normalizado, # <-- CÓDIGO NORMALIZADO (salva no DB)
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
    
    # --- MUDANÇA HTMX ---
    campanha = db_campanha.get_campaign_by_id(campanha_id)
    produtos = db_campanha_produtos.get_products_by_campaign_id(campanha_id)
    return render_template(
        'campanha/produtos_campanha.html', 
        active_page='campanhas_gestao', 
        campanha=campanha, 
        produtos=produtos
    )

@campanha_produtos_bp.route('/<int:campanha_id>/produtos/atualizar', methods=['POST'])
def atualizar_produtos(campanha_id):
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
                request.form.get('descricao_{}'.format(pid)),
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
    
    # --- MUDANÇA HTMX ---
    campanha = db_campanha.get_campaign_by_id(campanha_id)
    produtos = db_campanha_produtos.get_products_by_campaign_id(campanha_id)
    return render_template(
        'campanha/produtos_campanha.html', 
        active_page='campanhas_gestao', 
        campanha=campanha, 
        produtos=produtos
    )

@campanha_produtos_bp.route('/<int:campanha_id>/produtos/deletar', methods=['POST'])
def deletar_produtos(campanha_id):
    # --- NOVO: Verificação de Senha para Deleção em Massa ---
    confirmation_password = request.form.get('confirmation_password_bulk')
    if confirmation_password != DELETE_PASSWORD:
        flash('Senha de confirmação incorreta para deleção em massa.', 'danger')
    else:
        selecionados = request.form.getlist('selecionado')
        if not selecionados:
            flash('Nenhum produto selecionado para deletar.', 'warning')
        else:
            rowcount, error = db_campanha_produtos.delete_products_in_bulk(selecionados)
            if error: flash(f'Erro ao deletar produtos: {error}', 'danger')
            else: flash(f'{rowcount} produto(s) deletado(s) com sucesso!', 'success')

    # --- MUDANÇA HTMX ---
    campanha = db_campanha.get_campaign_by_id(campanha_id)
    produtos = db_campanha_produtos.get_products_by_campaign_id(campanha_id)
    return render_template(
        'campanha/produtos_campanha.html', 
        active_page='campanhas_gestao', 
        campanha=campanha, 
        produtos=produtos
    )

@campanha_produtos_bp.route('/<int:campanha_id>/produtos/validar_gtins', methods=['POST'])
def validar_gtins(campanha_id):
    data = request.get_json()
    products_data = data.get('products', []) # Espera [{id: '1', gtin: '123'}]

    if not products_data:
        return jsonify({"error": "Nenhum produto enviado"}), 400

    # 1. Extrai GTINs para validação e busca de CI
    #    Usa o GTIN limpo (sem padding)
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
        # Só atualiza se o GTIN limpo foi encontrado no mapa de CIs principais
        if gtin_limpo in ci_map_raw:
            cb_normalizado = pad_barcode(gtin_limpo) # Calcula o GTIN de 14 dígitos
            ci = ci_map_raw.get(gtin_limpo)
            
            # Tupla: (cb, cbn, ci, id)
            produtos_para_atualizar.append((
                gtin_limpo,       # codigo_barras (usamos o limpo/raw)
                cb_normalizado, # codigo_barras_normalizado
                ci,             # codigo_interno
                product_id      # id
            ))

    # 5. Executa o Update no banco
    updated_count = 0
    if produtos_para_atualizar:
        # Chama a nova função do DB
        rowcount, error_update = db_campanha_produtos.update_product_ci_bulk(produtos_para_atualizar)
        if error_update:
            # Não falha a requisição inteira, apenas avisa no console
            print(f"Erro ao atualizar CIs em campanha_produtos_db: {error_update}")
        else:
            updated_count = rowcount

    # 6. Retorna a lista de GTINs válidos (para UI) e a contagem de updates
    return jsonify({
        "valid_gtins": list(validos_raw_set),
        "updated_count": updated_count
    })

# --- NOVA ROTA DE EXPORTAÇÃO ---
@campanha_produtos_bp.route('/<int:campanha_id>/exportar')
def exportar_produtos(campanha_id):
    try:
        # 1. Buscar nome da campanha (para nome do arq)
        campanha = db_campanha.get_campaign_by_id(campanha_id)
        campanha_nome = campanha.nome if campanha else f"campanha_{campanha_id}"
        
        # 2. Buscar dados dos produtos
        produtos_data = db_campanha_produtos.get_products_by_campaign_id(campanha_id)
        if not produtos_data:
            flash('Nenhum produto encontrado para exportar.', 'warning')
            return redirect(url_for('campanha_produtos.produtos_por_campanha', campanha_id=campanha_id))
        
        # 3. Converter para DataFrame
        produtos_list = [dict(row) for row in produtos_data]
        df = pd.DataFrame(produtos_list)

        # 4. Definir e Renomear colunas (INCLUINDO CODIGO_INTERNO)
        colunas_exportar = {
            "codigo_interno": "Codigo Interno",
            "codigo_barras": "CÓDIGO DE BARRAS",
            "descricao": "DESCRIÇÃO",
            "pontuacao": "PONTUAÇÃO",
            "preco_normal": "PREÇO NORMAL",
            "preco_desconto": "PREÇO COM DESCONTO",
            "rebaixe": "REBAIXE",
            "qtd_limite": "QTD LIMITE"
        }
        
        # Filtra o DF para ter apenas as colunas que existem no DF e queremos
        colunas_presentes = [col for col in colunas_exportar.keys() if col in df.columns]
        df_final = df[colunas_presentes].rename(columns=colunas_exportar)

        # 5. Criar arquivo em memória
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Produtos Campanha')
        output.seek(0)
        
        # 6. Enviar arquivo
        return send_file(
            output,
            as_attachment=True,
            download_name=f"export_produtos_campanha_{campanha_nome}.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        flash(f'Ocorreu um erro ao gerar o arquivo Excel: {e}', 'danger')
        return redirect(url_for('campanha_produtos.produtos_por_campanha', campanha_id=campanha_id))