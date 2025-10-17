# aplicacao_web_campanhas/app_campanha.py

import os
import pandas as pd
import numpy as np # Importe o numpy
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

import database_campanha as db
from config import SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.before_request
def before_first_request():
    db.create_tables()

@app.teardown_appcontext
def teardown_db(exception):
    db.close_db_connection(exception)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_page():
    if request.method == 'POST':
        campanha_id = request.form.get('campanha')
        if not campanha_id:
            flash('Por favor, selecione uma campanha.', 'danger')
            return redirect(request.url)

        if 'file' not in request.files:
            flash('Nenhum arquivo selecionado.', 'danger')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('Nenhum arquivo selecionado.', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            try:
                column_map = {
                    'CÓDIGO DE BARRAS': 'codigo_barras',
                    'DESCRIÇÃO': 'descricao',
                    'PONTUAÇÃO': 'pontuacao',
                    'PREÇO NORMAL': 'preco_normal',
                    'PREÇO COM DESCONTO': 'preco_desconto',
                    'REBAIXE': 'rebaixe',
                    'QTD LIMITE': 'qtd_limite'
                }
                
                df = pd.read_excel(file)
                df.rename(columns=column_map, inplace=True)
                
                # --- LINHA ADICIONADA PARA CORRIGIR O ERRO ---
                # Substitui todos os NaN (Not a Number) por None (que se torna NULL no banco)
                df = df.replace({np.nan: None})
                # ---------------------------------------------

                required_cols = column_map.values()
                if not all(col in df.columns for col in required_cols):
                    flash('A planilha não contém todas as colunas esperadas. Verifique o cabeçalho.', 'danger')
                    return redirect(request.url)

                produtos_para_inserir = []
                for _, row in df.iterrows():
                    produtos_para_inserir.append((
                        campanha_id,
                        row.get('codigo_barras'),
                        row.get('descricao'),
                        row.get('pontuacao'),
                        row.get('preco_normal'),
                        row.get('preco_desconto'),
                        row.get('rebaixe'),
                        row.get('qtd_limite')
                    ))
                
                if produtos_para_inserir:
                    rowcount, error = db.add_products_bulk(produtos_para_inserir)
                    if error:
                        flash(f'Erro ao salvar produtos: {error}', 'danger')
                    else:
                        flash(f'{rowcount} produtos processados e salvos com sucesso!', 'success')
                else:
                    flash('Nenhum produto encontrado na planilha.', 'warning')

            except Exception as e:
                flash(f'Ocorreu um erro ao processar o arquivo: {e}', 'danger')
            
            return redirect(url_for('upload_page'))

    campanhas = db.get_all_campaigns()
    return render_template('upload.html', active_page='upload', campanhas=campanhas)


@app.route('/campanhas', methods=['GET', 'POST'])
def gestao_campanhas():
    if request.method == 'POST':
        nome = request.form.get('nome')
        data_inicio = request.form.get('data_inicio')
        data_fim = request.form.get('data_fim')

        if not all([nome, data_inicio, data_fim]):
            flash('Todos os campos são obrigatórios.', 'danger')
        else:
            error = db.add_campaign(nome, data_inicio, data_fim)
            if error:
                flash(f'Erro ao criar campanha: {error}', 'danger')
            else:
                flash('Campanha criada com sucesso!', 'success')
        
        return redirect(url_for('gestao_campanhas'))

    campanhas = db.get_all_campaigns()
    return render_template('campanhas.html', active_page='campanhas', campanhas=campanhas)

@app.route('/campanhas/editar/<int:campaign_id>', methods=['POST'])
def editar_campanha(campaign_id):
    nome = request.form.get('nome_edit')
    data_inicio = request.form.get('data_inicio_edit')
    data_fim = request.form.get('data_fim_edit')

    if not all([nome, data_inicio, data_fim]):
        flash('Todos os campos são obrigatórios para a edição.', 'danger')
    else:
        _, error = db.update_campaign(campaign_id, nome, data_inicio, data_fim)
        if error:
            flash(f'Erro ao atualizar campanha: {error}', 'danger')
        else:
            flash('Campanha atualizada com sucesso!', 'success')
            
    return redirect(url_for('gestao_campanhas'))


@app.route('/campanhas/deletar/<int:campaign_id>', methods=['POST'])
def deletar_campanha(campaign_id):
    _, error = db.delete_campaign(campaign_id)
    if error:
        flash(f'Erro ao deletar campanha: {error}', 'danger')
    else:
        flash('Campanha deletada com sucesso!', 'success')
        
    return redirect(url_for('gestao_campanhas'))


@app.route('/campanha/<int:campanha_id>/produtos')
def produtos_por_campanha(campanha_id):
    campanha = db.get_campaign_by_id(campanha_id)
    if not campanha:
        flash('Campanha não encontrada.', 'danger')
        return redirect(url_for('gestao_campanhas'))
    
    produtos = db.get_products_by_campaign_id(campanha_id)
    return render_template('produtos_campanha.html', active_page='campanhas', campanha=campanha, produtos=produtos)

@app.route('/campanha/<int:campanha_id>/produtos/adicionar', methods=['POST'])
def adicionar_produto(campanha_id):
    try:
        dados_produto = (
            campanha_id,
            request.form.get('codigo_barras'),
            request.form.get('descricao'),
            request.form.get('pontuacao') or None,
            request.form.get('preco_normal') or None,
            request.form.get('preco_desconto') or None,
            request.form.get('rebaixe') or None,
            request.form.get('qtd_limite') or None
        )
        _, error = db.add_single_product(dados_produto)
        if error:
            flash(f'Erro ao adicionar produto: {error}', 'danger')
        else:
            flash('Novo produto adicionado com sucesso!', 'success')
    except Exception as e:
        flash(f'Ocorreu um erro inesperado: {e}', 'danger')
        
    return redirect(url_for('produtos_por_campanha', campanha_id=campanha_id))


@app.route('/campanha/<int:campanha_id>/produtos/atualizar', methods=['POST'])
def atualizar_produtos(campanha_id):
    selecionados = request.form.getlist('selecionado')
    if not selecionados:
        flash('Nenhum produto selecionado para atualizar.', 'warning')
        return redirect(url_for('produtos_por_campanha', campanha_id=campanha_id))

    produtos_para_atualizar = []
    for produto_id in selecionados:
        produtos_para_atualizar.append((
            request.form.get(f'codigo_barras_{produto_id}'),
            request.form.get(f'descricao_{produto_id}'),
            request.form.get(f'pontuacao_{produto_id}') or None,
            request.form.get(f'preco_normal_{produto_id}') or None,
            request.form.get(f'preco_desconto_{produto_id}') or None,
            request.form.get(f'rebaixe_{produto_id}') or None,
            request.form.get(f'qtd_limite_{produto_id}') or None,
            produto_id
        ))
    
    rowcount, error = db.update_products_in_bulk(produtos_para_atualizar)
    if error:
        flash(f'Erro ao atualizar produtos: {error}', 'danger')
    else:
        flash(f'{rowcount} produto(s) atualizado(s) com sucesso!', 'success')

    return redirect(url_for('produtos_por_campanha', campanha_id=campanha_id))


@app.route('/campanha/<int:campanha_id>/produtos/deletar', methods=['POST'])
def deletar_produtos(campanha_id):
    selecionados = request.form.getlist('selecionado')
    if not selecionados:
        flash('Nenhum produto selecionado para deletar.', 'warning')
        return redirect(url_for('produtos_por_campanha', campanha_id=campanha_id))

    rowcount, error = db.delete_products_in_bulk(selecionados)
    if error:
        flash(f'Erro ao deletar produtos: {error}', 'danger')
    else:
        flash(f'{rowcount} produto(s) deletado(s) com sucesso!', 'success')
        
    return redirect(url_for('produtos_por_campanha', campanha_id=campanha_id))

