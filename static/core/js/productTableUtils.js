// static/js/productTableUtils.js

window.ProductTableUtils = (function() {

    // --- FUNÇÕES DE VALIDAÇÃO ---

    /**
     * Valida o formato (comprimento) do código de barras em uma linha.
     */
    function validarLinhaFormatoCodigo(input) {
        const valor = input.value.trim();
        const row = input.closest('tr');
        if (!row) return;

        // Limpa erro anterior de formato
        row.classList.remove('row-error-length');

        if (valor === "") {
            return; // Vazio não é erro de formato
        }

        const len = valor.length;
        const eValido = (len === 7) || (len === 8) || (len === 12) || (len === 13);

        if (!eValido) {
            row.classList.add('row-error-length');
        }
    }

    /**
     * Valida os preços em uma linha baseado nas configurações.
     */
    function validarLinhaPreco(input, config) {
        const row = input.closest('tr');
        if (!row) return;

        const normalInput = row.querySelector(config.precoNormalSelector);
        const desconto1Input = row.querySelector(config.precoDesconto1Selector); // Ex: preco_desconto_ ou preco_geral_
        const desconto2Input = config.precoDesconto2Selector ? row.querySelector(config.precoDesconto2Selector) : null; // Ex: preco_cliente_

        if (!normalInput || !desconto1Input) return; // Precisa pelo menos do normal e do primeiro desconto

        const getPrice = (el) => {
            if (!el) return NaN; // Se o elemento não existir
            const val = el.value.replace(',', '.').trim();
            if (val === "") return 0; // "null" (string vazia) conta como 0
            return parseFloat(val); // Retorna o número ou NaN se for "abc"
        };

        const precoNormal = getPrice(normalInput);
        const precoDesconto1 = getPrice(desconto1Input);
        const precoDesconto2 = getPrice(desconto2Input); // getPrice(null) retorna NaN, o que é ok

        // 2. Limpa classes de validação de preço anteriores (vermelho E verde)
        // Isso previne que a linha fique verde (do GTIN) e vermelha (do Preço) ao mesmo tempo.
        // As validações de GTIN (`row-invalid`) serão tratadas pelo botão "Validar GTINs".
        row.classList.remove('row-error-price', 'row-valid');

        // 3. Se Preco Normal for "abc" (NaN), não podemos comparar.
        // (Nota: 0 não é NaN, então campos vazios (agora 0) serão validados)
        if (isNaN(precoNormal)) {
             return; // Deixa neutro, pois não é um número válido para comparar
        }

        // 4. Se chegamos aqui, Preco Normal é um número (incluindo 0).
        let isError = false;

        // Valida PrecoNormal vs PrecoDesconto1 (se PrecoDesconto1 for um número válido)
        if (!isNaN(precoDesconto1) && precoDesconto1 > precoNormal) {
            isError = true;
        }

        // Valida PrecoNormal vs PrecoDesconto2 (se PrecoDesconto2 for um número válido)
        // Só executa se não houver erro no Desconto1
        if (!isError && desconto2Input && !isNaN(precoDesconto2) && precoDesconto2 > precoNormal) {
             isError = true;
        }

        // 5. Aplica a classe de erro (vermelho) ou de sucesso (verde)
        if (isError) {
            row.classList.add('row-error-price');
        } else {
            // Se não houve erro (e o preço normal é um número), é válido.
            // Usamos 'row-valid' que já tem o estilo verde definido.
            row.classList.add('row-valid');
        }
        // --- FIM DA MODIFICAÇÃO ---
    }

    // --- FUNÇÕES DE VALIDAÇÃO GERAL ---

    function validarTodosCodigos(tableBody) {
        const todosBarcodes = tableBody.querySelectorAll('.barcode-input');
        todosBarcodes.forEach(input => {
            validarLinhaFormatoCodigo(input);
        });
    }

    function validarTodosPrecos(tableBody, config) {
        // Pega um dos inputs de preço de cada linha para iniciar a validação da linha
        const inputsParaValidar = tableBody.querySelectorAll(config.precoNormalSelector);
        inputsParaValidar.forEach(input => {
            validarLinhaPreco(input, config);
        });
    }

    function initBulkDeleteValidation(tableBody) {
        const deleteBtn = document.getElementById('btn-delete-products');
        const passwordInput = document.getElementById('password-bulk-delete');
        const selectAllCheckbox = document.getElementById('select-all-checkbox');
        const REQUIRED_PASSWORD = '123'; // Senha hardcoded
        
        if (!deleteBtn || !passwordInput || !selectAllCheckbox) return;
        
        const checkDeleteStatus = () => {
            // Pega todos os checkboxes de linhas que estão checados
            const checkedBoxes = tableBody.querySelectorAll('.edit-checkbox:checked');
            const hasChecked = checkedBoxes.length > 0;
            const isPasswordCorrect = passwordInput.value === REQUIRED_PASSWORD;
            
            // Habilita se houver itens selecionados E a senha estiver correta
            deleteBtn.disabled = !(hasChecked && isPasswordCorrect);
            
            // Se houver itens selecionados, muda a cor do botão de delete para indicar que algo será deletado
            if (hasChecked) {
                 deleteBtn.style.backgroundColor = 'var(--button-danger-color, #e74c3c)';
            } else {
                 deleteBtn.style.backgroundColor = '#cccccc'; // Cor de disabled
            }
        };

        // Adiciona listeners para todos os eventos relevantes
        tableBody.addEventListener('change', checkDeleteStatus);
        selectAllCheckbox.addEventListener('change', checkDeleteStatus);
        passwordInput.addEventListener('input', checkDeleteStatus);
    }

    // --- INICIALIZAÇÃO E LISTENERS ---

    function initProductTable(config) {
        const table = document.querySelector(config.tableSelector);
        if (!table) {
            console.error("Tabela não encontrada com o seletor:", config.tableSelector);
            return;
        }
        const tableBody = table.querySelector('tbody');
        if (!tableBody) {
             console.error("Corpo da tabela (tbody) não encontrado.");
            return;
        }

        // 1. Modal de Descrição (assunto-modal)
        initDescriptionModal();

        // 2. Checkboxes de Edição
        initEditCheckboxes(tableBody);

        // 3. Validação ao vivo (Input Listener)
        initInputValidation(tableBody, config);

        // 4. Botão Validar Formato
        initValidatePrecoButton(tableBody, config);

        // 5. Botão Limpar Validações
        initClearValidationButton(tableBody);

        // 6. Botão Exportar Excel
        initExportExcelButton(table, config); // Passa a tabela inteira e config

        // 7. Botão Validar GTINs (se URL configurada)
        if (config.validateGtinUrl) {
            initValidateGtinButton(tableBody, config);
        }
        
        // 8. NOVO: Validação para Deleção em Massa
        initBulkDeleteValidation(tableBody);
    }

    // --- Funções Auxiliares de Inicialização ---

    function initDescriptionModal() {
        const assuntoModal = document.getElementById('assunto-modal');
        if (assuntoModal) {
            const assuntoCells = document.querySelectorAll('.assunto-cell'); // Assume que a classe é a mesma
            const assuntoModalContent = document.getElementById('assunto-modal-content');
            const assuntoModalBtnClose = document.getElementById('assunto-modal-btn-close');

            if (!assuntoCells.length || !assuntoModalContent || !assuntoModalBtnClose) return;

            const showDescriptionModal = (e) => {
                const input = e.currentTarget.querySelector('input'); // Pega o input dentro da célula
                const fullText = input ? input.value : null;
                if (fullText) {
                    assuntoModalContent.textContent = fullText;
                    assuntoModal.classList.add('show-modal');
                }
            };
            const closeDescriptionModal = () => {
                assuntoModal.classList.remove('show-modal');
                assuntoModalContent.textContent = '';
            };
            assuntoCells.forEach(cell => cell.addEventListener('click', showDescriptionModal));
            assuntoModalBtnClose.addEventListener('click', closeDescriptionModal);
            assuntoModal.addEventListener('click', (event) => {
                if (event.target === assuntoModal) closeDescriptionModal();
            });
        }
    }

    function initEditCheckboxes(tableBody) {
        const checkboxes = tableBody.querySelectorAll('.edit-checkbox'); // Assume classe padrão
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const row = this.closest('tr');
                const inputs = row.querySelectorAll('input[type="text"], input[type="number"]'); // Ajuste seletor se necessário
                inputs.forEach(input => {
                    input.disabled = !this.checked;
                });
            });
        });
    }

    function initInputValidation(tableBody, config) {
        tableBody.addEventListener('input', function(event) {
            const target = event.target;
            if (!target) return;

            // Validação de Código de Barras (Formato)
            if (target.classList.contains('barcode-input')) { // Assume classe padrão
                validarLinhaFormatoCodigo(target);
                // Limpa validação de GTIN (do DB) ao digitar
                 const row = target.closest('tr');
                 if(row) row.classList.remove('row-valid', 'row-invalid');
            }

            // Validação de Preços (usa seletores da config)
             if (target.matches(config.precoNormalSelector) ||
                 target.matches(config.precoDesconto1Selector) ||
                 (config.precoDesconto2Selector && target.matches(config.precoDesconto2Selector)) )
            {
                validarLinhaPreco(target, config);
            }
        });
    }

    function initValidatePrecoButton(tableBody, config) {
        // 1. Procura pelo ID 'btn-validar-preco'
        const validatePrecoBtn = document.getElementById('btn-validar-preco');
        if (validatePrecoBtn) {
            validatePrecoBtn.addEventListener('click', () => {
                // Valida apenas os preços
                validarTodosPrecos(tableBody, config);
            });
        }

        // 2. Procura também pelo ID antigo 'btn-validar-formato' (para segurança)
        const validateFormatoBtn = document.getElementById('btn-validar-formato');
        if (validateFormatoBtn) {
            validateFormatoBtn.addEventListener('click', () => {
                // Valida códigos e preços
                validarTodosCodigos(tableBody);
                validarTodosPrecos(tableBody, config);
            });
        }
    }

    function initClearValidationButton(tableBody) {
        const clearValidationBtn = document.getElementById('btn-limpar-validacoes'); // Assume ID padrão
        if (clearValidationBtn) {
            clearValidationBtn.addEventListener('click', () => {
                const allRows = tableBody.querySelectorAll('tr');
                allRows.forEach(row => {
                    row.classList.remove(
                        'row-error-length', 'row-error-price',
                        'row-valid', 'row-invalid'
                        // 'row-valid' já está incluído, então a limpeza funcionará
                    );
                });
            });
        }
    }

    function initExportExcelButton(table, config) {
        const exportXlsxBtn = document.getElementById('btn-export-excel'); // Assume ID padrão
        if (exportXlsxBtn && typeof XLSX !== 'undefined') { // Verifica se SheetJS está carregado
            exportXlsxBtn.addEventListener('click', () => {
                const tbody = table.querySelector('tbody');
                if (!tbody || tbody.rows.length === 0) {
                    alert('Nenhum produto para exportar.');
                    return;
                }

                const data = [];
                // Usa os headers da configuração
                data.push(config.exportHeaders);

                Array.from(tbody.rows).forEach(row => {
                    const inputs = row.querySelectorAll('input[type="text"], input[type="number"]');
                    const rowData = [];

                    // Mapeia os inputs para os dados da linha baseado na configuração
                    config.exportValueSelectors.forEach(selectorInfo => {
                        const input = row.querySelector(selectorInfo.selector);
                        let valueStr = input ? input.value : '';

                        if (selectorInfo.isNumeric) {
                             if (valueStr === null || valueStr === '') {
                                 rowData.push(null);
                             } else {
                                const correctedStr = valueStr.replace(',', '.');
                                const num = selectorInfo.isInteger ? parseInt(correctedStr, 10) : parseFloat(correctedStr);
                                rowData.push(isNaN(num) ? valueStr : num); // Mantém como string se falhar
                             }
                        } else {
                            rowData.push(valueStr); // Adiciona como string
                        }
                    });
                    data.push(rowData);
                });

                try {
                    const worksheet = XLSX.utils.aoa_to_sheet(data);

                    // Aplica formatos numéricos (usando config)
                    const range = XLSX.utils.decode_range(worksheet['!ref']);
                    for (let R = 1; R <= range.e.r; ++R) { // Linha 1 = dados
                         config.exportFormatConfig.forEach(formatInfo => {
                            const cell = worksheet[XLSX.utils.encode_cell({c: formatInfo.colIndex, r: R})];
                            // Aplica formato apenas se a célula existir e for numérica
                            if(cell && cell.t === 'n') {
                                cell.z = formatInfo.format;
                            }
                         });
                    }

                    const workbook = XLSX.utils.book_new();
                    XLSX.utils.book_append_sheet(workbook, worksheet, config.exportSheetName || "Produtos");
                    XLSX.writeFile(workbook, config.exportFileName || "export.xlsx");

                } catch (error) {
                    console.error("Erro ao gerar o arquivo XLSX:", error);
                    alert("Ocorreu um erro ao gerar o arquivo Excel. Verifique o console.");
                }
            });
        } else if (exportXlsxBtn) {
             console.error("SheetJS (xlsx) não está carregado. Não é possível exportar para .xlsx.");
             alert("Erro: A biblioteca para exportar Excel não foi carregada.");
        }
    }

    function initValidateGtinButton(tableBody, config) {
        const validateGtinBtn = document.getElementById('btn-validar-gtins'); // Assume ID padrão
        if (!validateGtinBtn) return;

        // Tenta pegar o ID da campanha/tabloide da URL de forma genérica
        // Exemplo: /campanha/123/produtos ou /tabloide/45/produtos
        const urlMatch = window.location.pathname.match(/\/(campanha|tabloide)\/(\d+)\/produtos/);
        const entityId = urlMatch ? urlMatch[2] : null;

        if (!entityId) {
             console.error("Não foi possível extrair o ID da Campanha/Tabloide da URL:", window.location.pathname);
             if (validateGtinBtn) {
                validateGtinBtn.disabled = true;
                validateGtinBtn.textContent = "Erro: ID não encontrado na URL";
             }
             return; // Não adiciona o listener se não encontrar ID
        }

         // Constrói a URL da API dinamicamente
         const apiUrl = config.validateGtinUrl.replace('{id}', entityId);

        validateGtinBtn.addEventListener('click', async () => {
            const originalText = validateGtinBtn.textContent;
            validateGtinBtn.textContent = 'Validando...';
            validateGtinBtn.disabled = true;

            const allBarcodeInputs = tableBody.querySelectorAll('.barcode-input'); // Assume classe padrão
            
            // --- CORREÇÃO ESTÁ AQUI ---
            // 1. Mapeia GTINs e IDs dos produtos
            const productsData = Array.from(allBarcodeInputs).map(input => {
                const row = input.closest('tr');
                const checkbox = row.querySelector('.edit-checkbox');
                const productId = checkbox ? checkbox.value : null;
                return {
                    id: productId,
                    gtin: input.value.trim()
                };
            }).filter(p => p.id); // Envia apenas produtos que têm ID (ignora o "adicionar novo")

            // Não envia nada se não houver o que validar
            if (productsData.length === 0) {
                validateGtinBtn.textContent = originalText;
                validateGtinBtn.disabled = false;
                return;
            }
            // --- FIM DA CORREÇÃO ---

            try {
                const response = await fetch(apiUrl, { // Usa a URL construída
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    // 2. Erro estava aqui: A variável agora é 'productsData'
                    body: JSON.stringify({ products: productsData })
                });

                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`Erro do servidor (${response.status}): ${errorText}`);
                }

                const result = await response.json();
                if (result.error) {
                     throw new Error(`Erro da API: ${result.error}`);
                }

                const validGtinSet = new Set(result.valid_gtins || []); // Garante que seja um array

                // 3. A lógica de colorir a linha permanece a mesma
                allBarcodeInputs.forEach(input => {
                    const gtin = input.value.trim();
                    const row = input.closest('tr');
                    if (!row) return;

                    row.classList.remove('row-valid', 'row-invalid'); // Limpa status anterior

                    if (gtin === "") return; // Ignora vazios

                    if (validGtinSet.has(gtin)) {
                        row.classList.add('row-valid');
                    } else {
                        row.classList.add('row-invalid');
                    }
                });

                // 4. Alerta o usuário sobre a atualização do CI no banco
                if (result.updated_count > 0) {
                    alert(`${result.updated_count} produto(s) tiveram o Código Interno atualizado no banco de dados.`);
                }
                // --- FIM DA MUDANÇA ---

            } catch (error) {
                console.error("Falha ao validar GTINs:", error);
                alert(`Ocorreu um erro ao validar os GTINs: ${error.message}`);
            } finally {
                validateGtinBtn.textContent = originalText;
                validateGtinBtn.disabled = false;
            }
        });
    }


    // Expõe a função de inicialização
    return {
        init: initProductTable
    };

})(); // Fim do Módulo ProductTableUtils