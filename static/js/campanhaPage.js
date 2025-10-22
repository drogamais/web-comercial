// aplicacao_web_campanhas/static/js/campanhaPage.js

document.addEventListener('DOMContentLoaded', () => {
    const editModal = document.getElementById('edit-modal');
    if (!editModal) return;

    const modalBtnCancel = document.getElementById('modal-btn-cancel');
    const editButtons = document.querySelectorAll('.btn-edit');
    const editForm = document.getElementById('edit-form');
    const nomeInput = document.getElementById('nome_edit');
    const dataInicioInput = document.getElementById('data_inicio_edit');
    const dataFimInput = document.getElementById('data_fim_edit');

    // Função para mostrar o modal
    const showModal = (e) => {
        const button = e.currentTarget;
        const campaignId = button.dataset.id;
        const campaignName = button.dataset.nome;
        const campaignInicio = button.dataset.inicio;
        const campaignFim = button.dataset.fim;

        // CORRIGIDO: Adicionado prefixo /campanha
        editForm.action = `/campanha/editar/${campaignId}`;

        // Preenche os campos do formulário
        nomeInput.value = campaignName;
        dataInicioInput.value = campaignInicio;
        dataFimInput.value = campaignFim;

        // Mostra o modal
        editModal.classList.add('show-modal');
    };

    // Função para esconder o modal
    const closeModal = () => {
        editModal.classList.remove('show-modal');
    };

    // Adiciona os eventos
    editButtons.forEach(button => {
        button.addEventListener('click', showModal);
    });

    modalBtnCancel.addEventListener('click', closeModal);

    // Fecha o modal se clicar fora da área de conteúdo
    editModal.addEventListener('click', function(event) {
        if (event.target === this) {
            closeModal();
        }
    });

    // --- LÓGICA PARA O MODAL DE DELEÇÃO ---
    const deleteModal = document.getElementById('delete-modal');
    if (deleteModal) {
        const deleteButtons = document.querySelectorAll('.btn-delete');
        const deleteForm = document.getElementById('delete-form');
        const deleteModalBtnCancel = document.getElementById('delete-modal-btn-cancel');
        const deleteModalBtnConfirm = document.getElementById('delete-modal-btn-confirm'); 
        const campaignNameSpan = document.getElementById('delete-modal-campaign-name');
        const deleteInput = document.getElementById('delete-modal-input'); 

        let correctCampaignName = ''; 

        // Função para mostrar o modal de deleção
        const showDeleteModal = (e) => {
            const button = e.currentTarget;
            const campaignId = button.dataset.id;
            correctCampaignName = button.dataset.nome; 

            // CORRIGIDO: Adicionado prefixo /campanha
            deleteForm.action = `/campanha/deletar/${campaignId}`;

            campaignNameSpan.textContent = correctCampaignName;

            deleteInput.value = '';
            deleteModalBtnConfirm.disabled = true;

            deleteModal.classList.add('show-modal');
        };

        const closeDeleteModal = () => {
            deleteModal.classList.remove('show-modal');
            correctCampaignName = ''; 
        };

        deleteInput.addEventListener('input', () => {
            if (deleteInput.value === correctCampaignName) {
                deleteModalBtnConfirm.disabled = false; 
            } else {
                deleteModalBtnConfirm.disabled = true; 
            }
        });

        deleteButtons.forEach(button => {
            button.addEventListener('click', showDeleteModal);
        });

        deleteModalBtnCancel.addEventListener('click', closeDeleteModal);

        deleteModal.addEventListener('click', function(event) {
            if (event.target === this) {
                closeDeleteModal();
            }
        });
    }
});

/**
 * Valida um único campo de código de barras e aplica/remove a classe de erro na linha.
 * @param {HTMLElement} input - O elemento input do código de barras.
 */
function validarLinhaProduto(input) {
    const valor = input.value.trim();
    const row = input.closest('tr');
    
    if (!row) return;

    if (valor === "") {
        row.classList.remove('row-error-length'); // MUDADO
        return;
    }
    
    const len = valor.length;
    const eValido = (len === 7) || (len === 8) || (len === 12) || (len === 13);

    if (eValido) {
        row.classList.remove('row-error-length'); // MUDADO
    } else {
        row.classList.add('row-error-length'); // MUDADO
    }
}

/**
 * Valida todos os códigos de barras na tabela.
 */
function validarTodosCodigos() {
    const todosBarcodes = document.querySelectorAll('.barcode-input');
    todosBarcodes.forEach(input => {
        validarLinhaProduto(input);
    });
}

/**
 * Valida os preços (desconto < normal) em uma linha.
 * @param {HTMLElement} input - O elemento input que acionou o evento.
 */
function validarLinhaPreco(input) {
    const row = input.closest('tr');
    if (!row) return;

    // Acessa os inputs pelos seus nomes (usando 'contém')
    const normalInput = row.querySelector('input[name*="preco_normal_"]');
    const descontoInput = row.querySelector('input[name*="preco_desconto_"]');

    if (!normalInput || !descontoInput) return;

    const precoNormal = parseFloat(normalInput.value);
    const precoDesconto = parseFloat(descontoInput.value);

    // Só valida se ambos forem números válidos
    if (!isNaN(precoNormal) && !isNaN(precoDesconto)) {
        // A regra: se o desconto for MAIOR que o normal, é um erro
        if (precoDesconto > precoNormal) {
            row.classList.add('row-error-price');
        } else {
            row.classList.remove('row-error-price');
        }
    } else {
        // Se um dos campos estiver vazio ou inválido, remove o erro
        row.classList.remove('row-error-price');
    }
}

/**
 * Valida todos os preços na tabela (chamada no load).
 */
function validarTodosPrecos() {
    // Pega um dos inputs de preço de cada linha (ex: preco_normal)
    const todosPrecosNormais = document.querySelectorAll('input[name*="preco_normal_"]');
    todosPrecosNormais.forEach(input => {
        // A função 'validarLinhaPreco' vai pegar a linha
        // e encontrar os dois campos de preço
        validarLinhaPreco(input);
    });
}

// --- Lógica Principal ---

document.addEventListener('DOMContentLoaded', function() {

    // --- LÓGICA DO MODAL DE DESCRIÇÃO (REUSANDO O 'assunto-modal') ---
    // Seleciona os mesmos elementos do seu outro projeto
    const assuntoModal = document.getElementById('assunto-modal');
    
    // Só executa se o modal existir na página
    if (assuntoModal) {
        const assuntoCells = document.querySelectorAll('.assunto-cell');
        const assuntoModalContent = document.getElementById('assunto-modal-content');
        const assuntoModalBtnClose = document.getElementById('assunto-modal-btn-close');

        // Função para mostrar o modal
        const showDescriptionModal = (e) => {
            // Pega o <input> que está DENTRO da célula clicada
            const input = e.currentTarget.querySelector('input');
            
            // Pega o texto do atributo 'value' do input
            const fullText = input ? input.value : null;

            if (fullText) {
                // Coloca o texto dentro do parágrafo do modal
                assuntoModalContent.textContent = fullText;
                
                // Mostra o modal
                assuntoModal.classList.add('show-modal');
            }
        };

        // Função para fechar o modal
        const closeDescriptionModal = () => {
            assuntoModal.classList.remove('show-modal');
            assuntoModalContent.textContent = ''; // Limpa o texto
        };

        // Adiciona o evento de clique em CADA célula com a classe
        assuntoCells.forEach(cell => {
            cell.addEventListener('click', showDescriptionModal);
        });

        // Evento para fechar no botão 'Fechar'
        assuntoModalBtnClose.addEventListener('click', closeDescriptionModal);

        // Evento para fechar ao clicar fora (no overlay)
        assuntoModal.addEventListener('click', function(event) {
            if (event.target === this) {
                closeDescriptionModal();
            }
        });
    }
    
    // 1. Lógica para habilitar/desabilitar edição ao clicar no checkbox
    //    (Baseado no seu 'produtosPage.js')
    const checkboxes = document.querySelectorAll('.edit-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('click', function() {
            const row = this.closest('tr');
            const inputs = row.querySelectorAll('input[type="text"], input[type="number"]');
            
            inputs.forEach(input => {
                if (this.checked) {
                    input.removeAttribute('disabled');
                } else {
                    input.setAttribute('disabled', 'disabled');
                }
            });
        });
    });

    // 3. Adiciona validação "ao vivo" (quando o usuário digita)
    // Adiciona validação "ao vivo" (quando o usuário digita)
    const tableBody = document.querySelector('table tbody');
    if (tableBody) {
        tableBody.addEventListener('input', function(event) {
            const target = event.target;
            
            // Validação de Código de Barras (Comprimento)
            if (target.classList.contains('barcode-input')) {
                validarLinhaProduto(target);
            }
            
            // NOVO - Validação de Preços (Desconto vs Normal)
            // Procura por inputs de preco_normal ou preco_desconto
            if (target.matches('input[name*="preco_normal_"]') || 
                target.matches('input[name*="preco_desconto_"]')) {
                validarLinhaPreco(target);
            }
        })
    }
    
    // --- NOVA LÓGICA PARA O BOTÃO DE VALIDAR FORMATO ---
    const validateFormatoBtn = document.getElementById('btn-validar-formato');
    if (validateFormatoBtn) {
        validateFormatoBtn.addEventListener('click', () => {
            // Simplesmente chama as duas funções de validação
            validarTodosCodigos();
            validarTodosPrecos();
        });

    
    // --- LÓGICA DO NOVO BOTÃO DE LIMPAR VALIDAÇÕES ---
    const clearValidationBtn = document.getElementById('btn-limpar-validacoes');
    
    if (clearValidationBtn) {
        clearValidationBtn.addEventListener('click', () => {
            // 1. Seleciona todas as linhas da tabela
            const allRows = document.querySelectorAll('table tbody tr');
            
            // 2. Itera por cada linha e remove todas as classes de validação
            allRows.forEach(row => {
                row.classList.remove(
                    'row-error-length', // Erro de formato (comprimento GTIN)
                    'row-error-price',  // Erro de preço (desconto > normal)
                    'row-valid',        // Válido no DB (verde)
                    'row-invalid'       // Inválido no DB (vermelho)
                );
            });
        });
    }

    // --- LÓGICA DO NOVO BOTÃO DE EXPORTAR EXCEL (.xlsx) USANDO SheetJS ---
    const exportXlsxBtn = document.getElementById('btn-export-excel'); 

    if (exportXlsxBtn) {
        exportXlsxBtn.addEventListener('click', () => {
            const table = document.querySelector('#form-edit-delete table');
            if (!table) {
                alert('Tabela de produtos não encontrada!');
                return;
            }

            const tbody = table.querySelector('tbody');
            if (!tbody || tbody.rows.length === 0) {
                alert('Nenhum produto para exportar.');
                return;
            }

            // --- Extração de Dados ---
            const data = [];
            const headers = [
                "Codigo Barras", "Descricao", "Pontos", 
                "Preco Normal", "Preco Desconto", "Rebaixe", "Qtd Limite"
            ];
            data.push(headers);

            Array.from(tbody.rows).forEach(row => {
                const inputs = row.querySelectorAll('input[type="text"], input[type="number"]');
                const rowData = [];
                
                const codigoBarras = inputs[0]?.value || '';
                const descricao = inputs[1]?.value || '';
                const pontuacaoStr = inputs[2]?.value || '';
                const precoNormalStr = inputs[3]?.value || '';
                const precoDescontoStr = inputs[4]?.value || '';
                const rebaixeStr = inputs[5]?.value || '';
                const qtdLimiteStr = inputs[6]?.value || '';

                // Função para converter para número, tratando vírgula como decimal
                const parseNumeric = (valueStr) => {
                    if (valueStr === null || valueStr === '') return null; 
                    const correctedStr = valueStr.replace(',', '.'); // Troca vírgula por ponto ANTES de converter
                    const num = parseFloat(correctedStr);
                    return isNaN(num) ? valueStr : num; 
                };
                 const parseIntNumeric = (valueStr) => {
                    if (valueStr === null || valueStr === '') return null;
                    const correctedStr = valueStr.replace(',', '.'); 
                    const num = parseInt(correctedStr, 10);
                     return isNaN(num) ? valueStr : num; 
                 };

                rowData.push(codigoBarras); 
                rowData.push(descricao);    
                rowData.push(parseIntNumeric(pontuacaoStr)); // Inteiro
                rowData.push(parseNumeric(precoNormalStr));  // Decimal
                rowData.push(parseNumeric(precoDescontoStr));// Decimal
                rowData.push(parseNumeric(rebaixeStr));      // Decimal
                rowData.push(parseIntNumeric(qtdLimiteStr)); // Inteiro
                
                data.push(rowData);
            });

            // --- Geração do XLSX com SheetJS ---
            try {
                const worksheet = XLSX.utils.aoa_to_sheet(data);
                
                // --- APLICAÇÃO DOS FORMATOS DE NÚMERO (COM VÍRGULA DECIMAL) ---
                // Formato Brasileiro: #.##0,00 -> Milhar com ponto, decimal com vírgula, 2 casas
                const formatDecimalBR = '#,##0.00'; // SheetJS usa ponto como decimal aqui, mas o Excel interpreta corretamente
                const formatInteger = '0'; 

                const range = XLSX.utils.decode_range(worksheet['!ref']);
                
                for (let R = 1; R <= range.e.r; ++R) { // Começa da linha 1 (dados)
                    // Coluna C (Pontos - Inteiro)
                    const cellC = worksheet[XLSX.utils.encode_cell({c: 2, r: R})];
                    if(cellC && cellC.t === 'n') cellC.z = formatInteger;
                    
                    // Coluna D (Preco Normal - Decimal BR)
                    const cellD = worksheet[XLSX.utils.encode_cell({c: 3, r: R})];
                    if(cellD && cellD.t === 'n') cellD.z = formatDecimalBR;
                    
                    // Coluna E (Preco Desconto - Decimal BR)
                    const cellE = worksheet[XLSX.utils.encode_cell({c: 4, r: R})];
                     if(cellE && cellE.t === 'n') cellE.z = formatDecimalBR;
                    
                    // Coluna F (Rebaixe - Decimal BR)
                    const cellF = worksheet[XLSX.utils.encode_cell({c: 5, r: R})];
                    if(cellF && cellF.t === 'n') cellF.z = formatDecimalBR;
                    
                     // Coluna G (Qtd Limite - Inteiro)
                    const cellG = worksheet[XLSX.utils.encode_cell({c: 6, r: R})];
                     if(cellG && cellG.t === 'n') cellG.z = formatInteger;
                }
                // --- FIM DA APLICAÇÃO DOS FORMATOS ---

                const workbook = XLSX.utils.book_new();
                XLSX.utils.book_append_sheet(workbook, worksheet, "Produtos");
                
                // Gera o arquivo XLSX
                XLSX.writeFile(workbook, "produtos_campanha_export.xlsx"); 

            } catch (error) {
                console.error("Erro ao gerar o arquivo XLSX:", error);
                alert("Ocorreu um erro ao gerar o arquivo Excel. Verifique o console.");
            }
        });
    }

    // 4. LÓGICA DO NOVO BOTÃO DE VALIDAÇÃO (dbDrogamais)
    const validateGtinBtn = document.getElementById('btn-validar-gtins');
    const formEditDelete = document.getElementById('form-edit-delete');
    
    if (validateGtinBtn && formEditDelete) {
        
        // Pega o ID da campanha pela URL do botão 'Salvar'
        const saveButton = formEditDelete.querySelector('button[formaction*="atualizar"]');
        let campanhaId = null;
        if (saveButton) {
            try {
                // Tenta extrair o ID da URL (ex: /campanha/123/produtos/atualizar)
                const match = saveButton.formAction.match(/\/campanha\/(\d+)\/produtos/);
                if (match) {
                    campanhaId = match[1];
                }
            } catch (e) {
                console.error("Não foi possível extrair o ID da campanha da URL do formulário.", e);
            }
        }

        if (!campanhaId) {
            console.error("Botão de validação não conseguiu encontrar o ID da campanha.");
            validateGtinBtn.disabled = true;
            validateGtinBtn.textContent = "Erro: ID da Campanha não encontrado";
        }

        validateGtinBtn.addEventListener('click', async () => {
            if (!campanhaId) return;
            
            const originalText = validateGtinBtn.textContent;
            validateGtinBtn.textContent = 'Validando...';
            validateGtinBtn.disabled = true;

            const allBarcodeInputs = document.querySelectorAll('.barcode-input');
            const allRows = document.querySelectorAll('table tbody tr');
            const gtins = Array.from(allBarcodeInputs).map(input => input.value);

            try {
                const response = await fetch(`/campanha/${campanhaId}/produtos/validar_gtins`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({ gtins: gtins })
                });

                if (!response.ok) {
                    throw new Error(`Erro do servidor: ${response.statusText}`);
                }

                const result = await response.json();
                
                // Cria um Set (lista rápida) de GTINs válidos
                const validGtinSet = new Set(result.valid_gtins);

                // Aplica os estilos
                allBarcodeInputs.forEach(input => {
                    const gtin = input.value.trim();
                    const row = input.closest('tr');
                    
                    // Limpa estilos antigos de validação
                    row.classList.remove('row-valid', 'row-invalid');

                    if (gtin === "") {
                        // Se estiver vazio, não faz nada
                        return;
                    }
                    
                    // Aplica o estilo (Válido ou Inválido)
                    if (validGtinSet.has(gtin)) {
                        row.classList.add('row-valid');
                    } else {
                        row.classList.add('row-invalid');
                    }
                });

            } catch (error) {
                console.error("Falha ao validar GTINs:", error);
                alert("Ocorreu um erro ao validar os GTINs. Verifique o console.");
            } finally {
                // Restaura o botão
                validateGtinBtn.textContent = originalText;
                validateGtinBtn.disabled = false;
            }
        });
    }
}});