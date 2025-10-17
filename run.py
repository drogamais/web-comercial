# aplicacao_web_atendimento/run.py

import sys
from waitress import serve
from app_campanha import app

# Verifica se o argumento "--dev" foi passado na linha de comandos
# Ex: python run.py --dev
is_dev_mode = "--dev" in sys.argv

if is_dev_mode:
    print("=" * 40)
    print(">>> EXECUTANDO EM MODO DE DESENVOLVIMENTO <<<")
    print(">>> O servidor irá reiniciar a cada alteração <<<")
    print("=" * 40)
    # Usa o servidor de desenvolvimento do Flask com debug=True (que ativa o auto-reload)
    # O host 0.0.0.0 permite aceder a partir de outras máquinas na mesma rede
    app.run(host='0.0.0.0', port=5001, debug=True)
else:
    print("=" * 40)
    print(">>> EXECUTANDO EM MODO DE PRODUÇÃO (WAITRESS) <<<")
    print("=" * 40)
    # Usa o servidor de produção Waitress (estável, sem auto-reload)

    serve(app, host='192.168.21.251', port=8080)