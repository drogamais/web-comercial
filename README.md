# Aplicação Web de Gestão de Atendimentos

Esta é uma aplicação web desenvolvida com Flask para registar, visualizar e editar atendimentos. O sistema foi desenhado para ser uma ferramenta interna, otimizando o fluxo de trabalho de diferentes tipos de registo, incluindo inserções padrão, de convénio e em massa para múltiplas lojas.

## Funcionalidades Principais

-   **Inserção de Atendimentos:** Formulários em grade para inserção rápida de múltiplos registos.
-   **Páginas Dedicadas:** Interfaces separadas para atendimentos Padrão e de Convênio.
-   **Inserção em Massa:** Uma funcionalidade para registar um mesmo tipo de atendimento para dezenas de lojas de uma só vez.
-   **Edição e Visualização:** Uma página para visualizar os registos recentes, com filtros por data e por responsável. Apenas registos dos últimos 3 dias podem ser editados.
-   **Interface Limpa:** O layout foi organizado para ser intuitivo e fácil de usar.

## Tecnologias Utilizadas

-   **Backend:** Python
-   **Framework Web:** Flask
-   **Servidor de Produção:** Waitress
-   **Banco de Dados:** MySQL (ligação via `mysql-connector-python`)
-   **Frontend:** HTML, CSS, JavaScript
-   **Templates:** Jinja2


## Pré-requisitos

-   Python 3.x
-   `pip` (gestor de pacotes do Python)
-   Acesso a um servidor de banco de dados MySQL.

## Como Instalar e Configurar o Ambiente

Siga estes passos para configurar o ambiente de desenvolvimento local:

1.  **Clonar o Repositório (se estiver no Git)**
    ```bash
    git clone <url_do_seu_repositorio>
    cd aplicacao_web_atendimento
    ```

2.  **Criar e Ativar o Ambiente Virtual (`venv`)**
    ```bash
    # Criar o venv
    python -m venv venv

    # Ativar no Windows
    venv\Scripts\activate

    # Ativar no macOS/Linux
    source venv/bin/activate
    ```

3.  **Instalar as Dependências**
    Com o ambiente virtual ativo, instale todas as bibliotecas necessárias com um único comando:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurar a Ligação ao Banco de Dados**
    Este projeto usa um ficheiro `config.py` para guardar as credenciais do banco de dados, que é ignorado pelo Git por segurança.
    -   Crie um ficheiro chamado `config.py` na raiz do projeto.
    -   Copie e cole o conteúdo abaixo, substituindo os valores pelos seus.

    ```python
    # aplicacao_web_atendimento/config.py

    SECRET_KEY = 'defina-uma-chave-secreta-forte-aqui'

    DB_CONFIG = {
        "user": "seu_usuario_do_banco",
        "password": "sua_senha_do_banco",
        "host": "ip_do_servidor_de_banco_de_dados",
        "port": 3306,
        "database": "dbSults",
        "collation": "utf8mb4_general_ci"
    }
    ```

## Como Executar a Aplicação

O ficheiro `run.py` foi configurado para iniciar a aplicação em dois modos diferentes:

#### Modo de Desenvolvimento
Este modo ativa o reinício automático do servidor a cada alteração no código, ideal para quando você está a programar.

```bash
python run.py --dev
```

Modo de Produção

Este modo usa o servidor waitress, que é mais estável e seguro. Use este modo para o ambiente final.

```bash
python run.py
```
