"""
Este arquivo define as rotas para o módulo 'tabloide' da aplicação.

Inclui rotas para:
- Upload de planilhas de produtos (Excel).
- Gerenciamento de Tabloides (Campanhas).
- Gerenciamento de Produtos por Tabloide (Adicionar, Editar, Deletar).
"""

import pandas as pd
import numpy as np
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
)
import os
import database.tabloide_db as db_tabloide  # Importa o banco de dados de tabloide
import database.common_db as db_common
from utils import allowed_file      # Reutiliza a função de utils

# Cria o Blueprint de Tabloide
tabloide_bp = Blueprint(
    'tabloide',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/tabloide'  # Prefixo /tabloide
)


@tabloide_bp.route('/upload', methods=['GET', 'POST'])
def upload_page():
    """
    Rota para a página de upload de planilhas de produtos.
    Processa o arquivo Excel (aba "Todos") e insere os produtos no banco.
    """
    if request.method == 'POST':
        # 1. Validações iniciais (Tabloide e Arquivo)
        tabloide_id = request.form.get('tabloide')
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
                # Define a relação: "Coluna no Excel" -> "Coluna no Banco de Dados"
                # As chaves (ex: 'GTIN') DEVEM ESTAR EM MAIÚSCULO, pois o código
                # abaixo converte todos os nomes de colunas do Excel para maiúsculo.
                column_map = {
                    'GTIN': 'codigo_barras',
                    'DESCRIÇÃO': 'descricao',
                    'LABORATÓRIO': 'laboratorio',
                    'PREÇO NORMAL': 'preco_normal',
                    'PREÇO DESCONTO GERAL': 'preco_desconto',
                    'PREÇO DESCONTO CLIENTE+': 'preco_desconto_cliente',
                    'TIPO DE REGRA': 'tipo_regra'
                    # A coluna "TIPO DE PREÇO" é ignorada, pois não está no mapa.
                }

                # --- 2. LEITURA DO EXCEL (LÓGICA MELHORADA) ---
                # Especifica 'sheet_name="Todos"'.
                # Seus arquivos de exemplo sugerem que o Excel original tem
                # múltiplas abas (Todos, Excluídos, Tabelas).
                # Se a aba principal tiver outro nome, altere o valor de 'sheet_name' aqui.
                try:
                    # Adiciona dtype={'GTIN': str} para forçar a leitura como texto
                    df = pd.read_excel(file, sheet_name='Todos', dtype={'GTIN': str})
                except Exception as e:
                    flash(f'Erro ao ler a planilha. Verifique se a aba "Todos" existe e se a coluna GTIN está presente. (Erro: {e})', 'danger')
                    return redirect(url_for('tabloide.upload_page'))

                # --- 3. LÓGICA DE LIMPEZA DE COLUNAS ---
                # Limpa os nomes das colunas do Excel antes de validar
                df.columns = (
                    df.columns.astype(str)
                    .str.replace(r'\s+', ' ', regex=True)  # Consolida espaços múltiplos
                    .str.replace(r'\s\+', '+', regex=True) # Remove espaço antes do +
                    .str.strip()                           # Limpa espaços nas bordas
                    .str.upper()                           # Força tudo para MAIÚSCULO
                )

                # --- 4. VALIDAÇÃO DAS COLUNAS (LÓGICA MELHORADA) ---
                # Verifica se as colunas ESPERADAS (do column_map)
                # existem no DataFrame DEPOIS da limpeza.
                required_source_cols = list(column_map.keys())
                missing_cols = [col for col in required_source_cols if col not in df.columns]

                if missing_cols:
                    # Esta mensagem agora informa ao usuário exatamente quais colunas
                    # (com base nos nomes do Excel) estão faltando.
                    flash(f'A planilha (aba "Todos") não contém todas as colunas esperadas. Faltando: {", ".join(missing_cols)}', 'danger')
                    return redirect(url_for('tabloide.upload_page'))

                # --- 5. PROCESSAMENTO DOS DADOS ---

                # 5.1. Renomeia as colunas para os nomes do banco de dados
                df = df.rename(columns=column_map)

                # 5.2. Substitui NaN por None (NULL para o banco)
                df = df.replace({np.nan: None})

                # 5.3. Converte colunas de preço para numérico
                # O 'errors="coerce"' transforma textos (ex: ' - ') em NaN,
                # que são então convertidos para None.
                cols_to_numeric = ['preco_normal', 'preco_desconto', 'preco_desconto_cliente']
                for col in cols_to_numeric:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce').replace({np.nan: None})

                # 5.4. Prepara os dados para inserção em lote
                produtos_para_inserir = [
                    (tabloide_id,
                     row.get('codigo_barras'),
                     row.get('descricao'),
                     row.get('laboratorio'),
                     row.get('preco_normal'),
                     row.get('preco_desconto'),
                     row.get('preco_desconto_cliente'),
                     row.get('tipo_regra')
                     )
                    for _, row in df.iterrows()
                ]

                # 5.5. Insere no banco de dados
                if produtos_para_inserir:
                    rowcount, error = db_tabloide.add_products_bulk(produtos_para_inserir)
                    if error:
                        flash(f'Erro ao salvar produtos: {error}', 'danger')
                    else:
                        flash(f'{rowcount} produtos processados e salvos com sucesso!', 'success')
                else:
                    flash('Nenhum produto encontrado na planilha.', 'warning')

            except Exception as e:
                flash(f'Ocorreu um erro inesperado ao processar o arquivo: {e}', 'danger')
            
            return redirect(url_for('tabloide.upload_page'))

    # Lógica para o método GET (carregar a página de upload)
    tabloides = db_tabloide.get_active_campaigns_for_upload()
    return render_template('tabloide/upload_tabloide.html', active_page='upload', tabloides=tabloides)

@tabloide_bp.route('/download_modelo')
def download_modelo():
    """
    Rota para baixar o arquivo .xlsx modelo para upload.
    """
    # O tabloide_bp.root_path aponta para a pasta 'routes'
    # '..' sobe um nível para a raiz do projeto
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
        # Redireciona de volta para a página anterior ou uma página padrão
        return redirect(request.referrer or url_for('tabloide.gestao_tabloides'))

# -----------------------------------------------------
# ROTAS DE GERENCIAMENTO DE TABLOIDES (CAMPANHAS)
# (O código original abaixo estava correto e foi mantido)
# -----------------------------------------------------

@tabloide_bp.route('/gerenciar', methods=['GET', 'POST'])
def gestao_tabloides():
    """
    Rota para criar e listar todos os tabloides (campanhas).
    """
    if request.method == 'POST':
        # Adicionar novo tabloide
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

    # GET: Exibe a página de gerenciamento
    tabloides = db_tabloide.get_all_campaigns()
    return render_template('tabloide/tabloides.html', active_page='tabloides', tabloides=tabloides)


@tabloide_bp.route('/editar/<int:campaign_id>', methods=['POST'])
def editar_tabloide(campaign_id):
    """
    Rota para editar um tabloide (campanha) existente.
    """
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
    """
    Rota para desativar (deletar) um tabloide (campanha).
    """
    _, error = db_tabloide.delete_campaign(campaign_id)
    if error:
        flash(f'Erro ao desativar tabloide: {error}', 'danger')
    else:
        flash('Tabloide desativado com sucesso!', 'success')
    return redirect(url_for('tabloide.gestao_tabloides'))

# -----------------------------------------------------
# ROTAS DE GERENCIAMENTO DE PRODUTOS (POR TABLOIDE)
# (O código original abaixo estava correto e foi mantido)
# -----------------------------------------------------

@tabloide_bp.route('/<int:campanha_id>/produtos')
def produtos_por_tabloide(campanha_id):
    """
    Rota para listar todos os produtos de um tabloide específico.
    """
    tabloide = db_tabloide.get_campaign_by_id(campanha_id)
    if not tabloide:
        flash('Tabloide não encontrado.', 'danger')
        return redirect(url_for('tabloide.gestao_tabloides'))

    produtos = db_tabloide.get_products_by_campaign_id(campanha_id)
    return render_template('tabloide/produtos_tabloide.html', active_page='tabloides', tabloide=tabloide, produtos=produtos)


@tabloide_bp.route('/<int:campanha_id>/produtos/adicionar', methods=['POST'])
def adicionar_produto(campanha_id):
    """
    Rota para adicionar um único produto manualmente a um tabloide.
    """
    try:
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
        _, error = db_tabloide.add_single_product(dados_produto)
        if error:
            flash(f'Erro ao adicionar produto: {error}', 'danger')
        else:
            flash('Novo produto adicionado com sucesso!', 'success')
    except Exception as e:
        flash(f'Ocorreu um erro inesperado: {e}', 'danger')
    return redirect(url_for('tabloide.produtos_por_tabloide', campanha_id=campanha_id))


@tabloide_bp.route('/<int:campanha_id>/produtos/atualizar', methods=['POST'])
def atualizar_produtos(campanha_id):
    """
    Rota para atualizar múltiplos produtos de um tabloide em lote.
    """
    selecionados = request.form.getlist('selecionado')
    if not selecionados:
        flash('Nenhum produto selecionado para atualizar.', 'warning')
        return redirect(url_for('tabloide.produtos_por_tabloide', campanha_id=campanha_id))

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

    rowcount, error = db_tabloide.update_products_in_bulk(produtos_para_atualizar)
    if error:
        flash(f'Erro ao atualizar produtos: {error}', 'danger')
    else:
        flash(f'{rowcount} produto(s) atualizado(s) com sucesso!', 'success')
    return redirect(url_for('tabloide.produtos_por_tabloide', campanha_id=campanha_id))


@tabloide_bp.route('/<int:campanha_id>/produtos/deletar', methods=['POST'])
def deletar_produtos(campanha_id):
    """
    Rota para deletar múltiplos produtos de um tabloide em lote.
    """
    selecionados = request.form.getlist('selecionado')
    if not selecionados:
        flash('Nenhum produto selecionado para deletar.', 'warning')
        return redirect(url_for('tabloide.produtos_por_tabloide', campanha_id=campanha_id))

    rowcount, error = db_tabloide.delete_products_in_bulk(selecionados)
    if error:
        flash(f'Erro ao deletar produtos: {error}', 'danger')
    else:
        flash(f'{rowcount} produto(s) deletado(s) com sucesso!', 'success')
    return redirect(url_for('tabloide.produtos_por_tabloide', campanha_id=campanha_id))

# --- NOVA ROTA PARA VALIDAR GTINS (TABLOIDE) ---
@tabloide_bp.route('/<int:tabloide_id>/produtos/validar_gtins', methods=['POST'])
def validar_gtins_tabloide(tabloide_id):
    """
    Recebe GTINs, valida no dbDrogamais e retorna os válidos.
    Usa a função de validação do módulo common_db.
    """
    data = request.get_json()
    gtins_raw = data.get('gtins', [])

    if not gtins_raw:
        return jsonify({"error": "Nenhum GTIN enviado"}), 400

    gtins_para_validar_raw = [gtin for gtin in gtins_raw if gtin and gtin.strip()]
    if not gtins_para_validar_raw:
        return jsonify({"valid_gtins": []})

    gtins_padded = [g.zfill(14) for g in gtins_para_validar_raw]
    map_padded_to_raw = {padded: raw for padded, raw in zip(gtins_padded, gtins_para_validar_raw)}

    # Chama a função do módulo comum
    validos_padded, error = db_common.validate_gtins_in_external_db(gtins_padded) # <-- Atualizado aqui

    if error:
        error_message = f"Erro ao validar GTINs no banco externo: {error}"
        print(f"Erro na rota validar_gtins_tabloide: {error_message}")
        return jsonify({"error": error_message}), 500

    validos_raw = {map_padded_to_raw[padded_gtin] for padded_gtin in validos_padded if padded_gtin in map_padded_to_raw}

    return jsonify({"valid_gtins": list(validos_raw)})