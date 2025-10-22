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

        const precoNormal = parseFloat(normalInput.value.replace(',', '.')); // Trata vírgula
        const precoDesconto1 = parseFloat(desconto1Input.value.replace(',', '.'));
        const precoDesconto2 = desconto2Input ? parseFloat(desconto2Input.value.replace(',', '.')) : NaN;

        // Limpa erro anterior de preço
        row.classList.remove('row-error-price');

        let isError = false;

        // Valida PrecoNormal vs PrecoDesconto1 (se PrecoDesconto1 for um número válido)
        if (!isNaN(precoNormal) && !isNaN(precoDesconto1)) {
            if (precoDesconto1 > precoNormal) {
                isError = true;
            }
        }

        // Se NÃO houve erro e PrecoDesconto1 está VAZIO/INVÁLIDO,
        // valida PrecoNormal vs PrecoDesconto2 (se existir e for um número válido)
        if (!isError && (isNaN(precoDesconto1) || desconto1Input.value.trim() === '') && desconto2Input && !isNaN(precoDesconto2)) {
             if (!isNaN(precoNormal)) {
                if (precoDesconto2 > precoNormal) {
                    isError = true;
                }
             }
        }

        // Aplica a classe de erro se necessário
        if (isError) {
            row.classList.add('row-error-price');
        }
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
        initValidateFormatButton(tableBody, config);

        // 5. Botão Limpar Validações
        initClearValidationButton(tableBody);

        // 6. Botão Exportar Excel
        initExportExcelButton(table, config); // Passa a tabela inteira e config

        // 7. Botão Validar GTINs (se URL configurada)
        if (config.validateGtinUrl) {
            initValidateGtinButton(tableBody, config);
        }
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
            checkbox.addEventListener('click', function() {
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

    function initValidateFormatButton(tableBody, config) {
        const validateFormatoBtn = document.getElementById('btn-validar-formato'); // Assume ID padrão
        if (validateFormatoBtn) {
            validateFormatoBtn.addEventListener('click', () => {
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
            const gtins = Array.from(allBarcodeInputs).map(input => input.value.trim());

            try {
                const response = await fetch(apiUrl, { // Usa a URL construída
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({ gtins: gtins })
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