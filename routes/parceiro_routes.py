[file: web-comercial/routes/parceiro_routes.py]
# routes/parceiro_routes.py

import io
import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
import database.parceiro_db as db
from utils import DELETE_PASSWORD # <-- Importa a senha
import services.parceiros_embedded_service as api_service
# -----------

# Campos principais do parceiro
PARCEIRO_FIELDS = (
    "nome_ajustado", "tipo", "cnpj", "nome_fantasia", "razao_social",
    "gestor", "telefone_gestor", "email_gestor"
)

parceiro_bp = Blueprint(
    'parceiro', __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/parceiro'
)

# --- NOVO: ROTA PARA EXPORTAR PARCEIROS ---
@parceiro_bp.route('/exportar')
def exportar_parceiros():
    try:
        # 1. Busca os mesmos filtros que a página principal usa
        tipo_filtro = request.args.get('tipo') or None
        nome_fantasia_filtro = request.args.get('nome_fantasia') or None 
        data_entrada_min_filtro = request.args.get('data_entrada_min') or None
        data_saida_max_filtro = request.args.get('data_saida_max') or None
        sort_expiring_filtro = request.args.get('sort_expiring') == '1' # ADICIONADO

        # 2. Busca os dados do banco (respeitando os filtros)
        parceiros_data = db.get_all_parceiros(
            tipo=tipo_filtro,
            nome_fantasia=nome_fantasia_filtro, 
            data_entrada_min=data_entrada_min_filtro,
            data_saida_max=data_saida_max_filtro,
            sort_by_expiration=sort_expiring_filtro # ADICIONADO
        )

        if not parceiros_data:
            flash('Nenhum parceiro encontrado para exportar (com base nos filtros atuais).', 'warning')
            return redirect(url_for('parceiro.gestao_parceiros'))

        # 3. Converte os dados para um DataFrame do Pandas
        #    (Convertemos de RowMapping para dict para o Pandas)
        parceiros_list = [dict(row) for row in parceiros_data]
        df = pd.DataFrame(parceiros_list)

        # 4. Limpa e Renomeia as colunas para um relatório amigável
        #    (Mapeia 1/0 para Sim/Não)
        if 'status' in df.columns:
            df['status'] = df['status'].apply(lambda x: 'Ativo' if x == 1 else 'Inativo')
        
        if 'senha_definida' in df.columns:
             df['senha_definida'] = df['senha_definida'].apply(lambda x: 'Sim' if x == 1 else 'Não')

        # Define a ordem e os nomes das colunas no Excel
        colunas_exportar = {
            "id": "ID Local",
            "api_user_id": "ID API (Embedded)",
            "nome_fantasia": "Nome Fantasia",
            "tipo": "Tipo",
            "cnpj": "CNPJ",
            "nome_ajustado": "Nome Ajustado",
            "razao_social": "Razão Social",
            "gestor": "Gestor",
            "telefone_gestor": "Telefone Gestor",
            "email_gestor": "Email Gestor",
            "data_entrada": "Data Entrada",
            "data_saida": "Data Saída",
            "senha_definida": "Senha Definida",
            "data_atualizacao": "Última Atualização"
        }
        
        # Filtra o DataFrame para ter apenas as colunas que queremos e na ordem certa
        df_final = df[list(colunas_exportar.keys())].rename(columns=colunas_exportar)

        # 5. Cria o arquivo Excel em memória
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Parceiros')
        
        output.seek(0) # Volta ao início do arquivo em memória

        # 6. Envia o arquivo para o usuário
        return send_file(
            output,
            as_attachment=True,
            download_name="export_parceiros.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        flash(f'Ocorreu um erro ao gerar o arquivo Excel: {e}', 'danger')
        return redirect(url_for('parceiro.gestao_parceiros'))

def _get_form_data(form, sufixo=""):
    """Extrai e normaliza os dados do formulário."""
    data = {field: (form.get(f"{field}{sufixo}") or None) for field in PARCEIRO_FIELDS}
    data["data_entrada"] = form.get(f"data_entrada{sufixo}") or None
    data["data_saida"] = form.get(f"data_saida{sufixo}") or None
    data["status"] = 1
    return data

# --- ROTA DE GESTÃO (GET e POST/CREATE) ---
@parceiro_bp.route('/gerenciar', methods=['GET', 'POST'])
def gestao_parceiros():
    if request.method == 'POST':
        
        data = _get_form_data(request.form)
        user_email_para_api = data.get('email_gestor') # Guardamos para o rollback

        if not data["nome_ajustado"]:
            flash('O campo "Nome Ajustado" é obrigatório.', 'danger')
            # --- MUDANÇA HTMX ---
            # (continua para re-renderizar)
        else:
            try:
                # 1. Chama o serviço para fazer todo o processo da API
                api_id, erro_api = api_service.criar_parceiro_completo(data)
                
                if erro_api:
                    flash(f'Erro ao cadastrar parceiro na API Embedded: {erro_api}', 'danger')
                else:
                    # 2. Se a API funcionou, salva no banco local
                    data['api_user_id'] = api_id 
                    error_db = db.add_parceiro(**data)
                    
                    if error_db:
                        # Se falhar no banco, desfaz a criação do usuário na API
                        api_service.rollback_criacao_usuario(user_email_para_api)
                        flash(f'Parceiro salvo na API, mas falhou ao salvar localmente: {error_db}. O cadastro na API foi revertido.', 'danger')
                    else:
                        flash('Parceiro criado e vinculado ao grupo com sucesso!', 'success')
            
            except Exception as e:
                # Se algo inesperado acontecer, tenta reverter
                api_service.rollback_criacao_usuario(user_email_para_api)
                flash(f'Um erro inesperado ocorreu: {e}. O cadastro foi revertido.', 'danger')
            
        # --- MUDANÇA HTMX ---
        # REMOVIDO: return redirect(url_for('parceiro.gestao_parceiros'))

    # --- LÓGICA GET (ou continuação do POST) ---
    (parceiros, tipo_filtro, nome_fantasia_filtro, 
     data_entrada_min_filtro, data_saida_max_filtro,
     sort_expiring_filtro, expiring_ids_set) = _get_parceiros_filtrados(request)
    
    return render_template(
        'parceiro/parceiros.html',
        active_page='parceiros_gestao',
        parceiros=parceiros,
        tipo_filtro=tipo_filtro,
        nome_fantasia_filtro=nome_fantasia_filtro, 
        data_entrada_min_filtro=data_entrada_min_filtro,
        data_saida_max_filtro=data_saida_max_filtro,
        sort_expiring_filtro=sort_expiring_filtro, 
        expiring_ids_set=expiring_ids_set          
    )

def _get_parceiros_filtrados(request_obj):
    """Função auxiliar para buscar parceiros filtrados (usado no GET)."""
    tipo_filtro = request_obj.args.get('tipo') or None
    nome_fantasia_filtro = request_obj.args.get('nome_fantasia') or None 
    data_entrada_min_filtro = request_obj.args.get('data_entrada_min') or None
    data_saida_max_filtro = request_obj.args.get('data_saida_max') or None
    sort_expiring_filtro = request_obj.args.get('sort_expiring') == '1'
    
    expiring_partners = db.get_expiring_parceiros(days_ahead=30)
    expiring_ids_set = {p['id'] for p in expiring_partners}

    parceiros = db.get_all_parceiros(
        tipo=tipo_filtro,
        nome_fantasia=nome_fantasia_filtro, 
        data_entrada_min=data_entrada_min_filtro,
        data_saida_max=data_saida_max_filtro,
        sort_by_expiration=sort_expiring_filtro
    )
    
    return (parceiros, tipo_filtro, nome_fantasia_filtro, 
            data_entrada_min_filtro, data_saida_max_filtro,
            sort_expiring_filtro, expiring_ids_set) 


# --- ROTA DE EDIÇÃO (UPDATE) ---
@parceiro_bp.route('/editar/<int:parceiro_id>', methods=['POST'])
def editar_parceiro(parceiro_id):
    
    data = _get_form_data(request.form, sufixo="_edit")

    if not data["nome_ajustado"]:
        flash('O campo "Nome Ajustado" é obrigatório para a edição.', 'danger')
    else:
        parceiro_atual = db.get_parceiro_by_id(parceiro_id)
        email_antigo = parceiro_atual.get('email_gestor')
        api_user_id = parceiro_atual.get('api_user_id') # Pega o ID da API
        email_novo = data.get('email_gestor')
        
        if email_antigo != email_novo:
            flash('Não é permitido alterar o "E-mail Gestor". A alteração do email foi ignorada.', 'warning')
            data['email_gestor'] = email_antigo

        try:
            # Chama o serviço de atualização
            sucesso_api, erro_api = api_service.atualizar_usuario(api_user_id, data)

            if not sucesso_api:
                flash(f'Erro ao atualizar parceiro na API Embedded: {erro_api}', 'danger')
            else:
                # Atualiza o banco local
                _, error_db = db.update_parceiro(parceiro_id, **data)
                
                if error_db:
                    flash(f'Parceiro atualizado na API, mas falhou ao salvar localmente: {error_db}', 'danger')
                else:
                    flash('Parceiro atualizado com sucesso (Sincronizado com Embedded)!', 'success')

        except Exception as e:
            flash(f'Um erro inesperado ocorreu ao editar: {e}', 'danger')

    # --- MUDANÇA HTMX ---
    (parceiros, tipo_filtro, nome_fantasia_filtro, 
     data_entrada_min_filtro, data_saida_max_filtro,
     sort_expiring_filtro, expiring_ids_set) = _get_parceiros_filtrados(request)
    
    return render_template(
        'parceiro/parceiros.html',
        active_page='parceiros_gestao',
        parceiros=parceiros,
        tipo_filtro=tipo_filtro,
        nome_fantasia_filtro=nome_fantasia_filtro, 
        data_entrada_min_filtro=data_entrada_min_filtro,
        data_saida_max_filtro=data_saida_max_filtro,
        sort_expiring_filtro=sort_expiring_filtro, 
        expiring_ids_set=expiring_ids_set          
    )


# --- ROTA DE DELEÇÃO (DELETE) ---
@parceiro_bp.route('/deletar/<int:parceiro_id>', methods=['POST'])
def deletar_parceiro(parceiro_id):
    
    confirmation_password = request.form.get('confirmation_password')
    if confirmation_password != DELETE_PASSWORD:
        flash('Senha de confirmação incorreta.', 'danger')
    else:
        # Pega o email ANTES de deletar o parceiro do banco
        parceiro = db.get_parceiro_by_id(parceiro_id)
        email_para_deletar = parceiro.get('email_gestor') if parceiro else None

        try:
            # Tenta deletar da API primeiro
            sucesso_api, erro_api = api_service.deletar_usuario(email_para_deletar)
            
            if not sucesso_api:
                flash(f'Erro ao deletar parceiro na API Embedded: {erro_api}', 'danger')
            else:
                # Se a API funcionou, deleta do banco local
                _, error_db = db.delete_parceiro(parceiro_id)
                
                if error_db:
                    flash(f'Parceiro deletado da API, mas falhou ao deletar localmente: {error_db}', 'danger')
                else:
                    flash('Parceiro deletado permanentemente com sucesso (Sincronizado com Embedded)!', 'success')
                
        except Exception as e:
            flash(f'Um erro inesperado ocorreu ao deletar: {e}', 'danger')

    # --- MUDANÇA HTMX ---
    (parceiros, tipo_filtro, nome_fantasia_filtro, 
     data_entrada_min_filtro, data_saida_max_filtro,
     sort_expiring_filtro, expiring_ids_set) = _get_parceiros_filtrados(request)
    
    return render_template(
        'parceiro/parceiros.html',
        active_page='parceiros_gestao',
        parceiros=parceiros,
        tipo_filtro=tipo_filtro,
        nome_fantasia_filtro=nome_fantasia_filtro, 
        data_entrada_min_filtro=data_entrada_min_filtro,
        data_saida_max_filtro=data_saida_max_filtro,
        sort_expiring_filtro=sort_expiring_filtro, 
        expiring_ids_set=expiring_ids_set          
    )

# --- ROTA DE DEFINIR SENHA (MODIFICADA) ---
@parceiro_bp.route('/definir-senha/<int:parceiro_id>', methods=['POST'])
def definir_senha(parceiro_id):
    
    nova_senha = request.form.get('nova_senha')
    confirmar_senha = request.form.get('confirmar_senha')

    if not nova_senha or not confirmar_senha:
        flash('Por favor, preencha os dois campos de senha.', 'danger')
    elif nova_senha != confirmar_senha:
        flash('As senhas não conferem.', 'danger')
    else:
        parceiro = db.get_parceiro_by_id(parceiro_id)
        if not parceiro or not parceiro.get('email_gestor'):
            flash('Parceiro não encontrado ou sem email cadastrado.', 'danger')
        else:
            email_do_parceiro = parceiro.get('email_gestor')
            try:
                # 1. Chama o serviço para definir a senha na API
                sucesso_api, erro_api = api_service.definir_senha_usuario(email_do_parceiro, nova_senha)

                if not sucesso_api:
                    flash(f'Erro ao definir senha na API Embedded: {erro_api}', 'danger')
                else:
                    # 2. Se a API funcionou, marca a flag no banco local
                    error_db = db.set_senha_definida_flag(parceiro_id)
                    
                    if error_db:
                         flash(f'Senha atualizada na API, mas falhou ao marcar status no banco local: {error_db}', 'warning')
                    else:
                         flash(f'Senha do usuário {email_do_parceiro} atualizada com sucesso!', 'success')

            except Exception as e:
                flash(f'Um erro inesperado ocorreu ao definir a senha: {e}', 'danger')

    # --- MUDANÇA HTMX ---
    (parceiros, tipo_filtro, nome_fantasia_filtro, 
     data_entrada_min_filtro, data_saida_max_filtro,
     sort_expiring_filtro, expiring_ids_set) = _get_parceiros_filtrados(request)
    
    return render_template(
        'parceiro/parceiros.html',
        active_page='parceiros_gestao',
        parceiros=parceiros,
        tipo_filtro=tipo_filtro,
        nome_fantasia_filtro=nome_fantasia_filtro, 
        data_entrada_min_filtro=data_entrada_min_filtro,
        data_saida_max_filtro=data_saida_max_filtro,
        sort_expiring_filtro=sort_expiring_filtro, 
        expiring_ids_set=expiring_ids_set          
    )