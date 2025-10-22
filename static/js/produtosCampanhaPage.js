// static/js/produtosCampanhaPage.js

document.addEventListener('DOMContentLoaded', function() {
    if (window.ProductTableUtils && window.ProductTableUtils.init) {

        // --- Configuração Específica da Página de Produtos de Campanha ---
        const config = {
            tableSelector: '#form-edit-delete table', // Seletor da tabela
            precoNormalSelector: 'input[name*="preco_normal_"]',
            precoDesconto1Selector: 'input[name*="preco_desconto_"]',
            precoDesconto2Selector: null, // Campanha não tem segundo preço de desconto relevante para validação direta
            validateGtinUrl: '/campanha/{id}/produtos/validar_gtins', // URL da API (com placeholder)
            exportHeaders: [ // Cabeçalhos para o Excel
                "Codigo Barras", "Descricao", "Pontos",
                "Preco Normal", "Preco Desconto", "Rebaixe", "Qtd Limite"
            ],
            exportValueSelectors: [ // Seletores na ordem dos cabeçalhos
                { selector: 'input[name*="codigo_barras_"]', isNumeric: false },
                { selector: 'input[name*="descricao_"]', isNumeric: false },
                { selector: 'input[name*="pontuacao_"]', isNumeric: true, isInteger: true },
                { selector: 'input[name*="preco_normal_"]', isNumeric: true, isInteger: false },
                { selector: 'input[name*="preco_desconto_"]', isNumeric: true, isInteger: false },
                { selector: 'input[name*="rebaixe_"]', isNumeric: true, isInteger: false },
                { selector: 'input[name*="qtd_limite_"]', isNumeric: true, isInteger: true }
            ],
            exportFormatConfig: [ // Formatação para colunas numéricas (índice baseado em exportHeaders)
                 { colIndex: 2, format: '0' },                 // Pontos (Inteiro)
                 { colIndex: 3, format: '#,##0.00' },          // Preco Normal (Decimal BR)
                 { colIndex: 4, format: '#,##0.00' },          // Preco Desconto (Decimal BR)
                 { colIndex: 5, format: '#,##0.00' },          // Rebaixe (Decimal BR)
                 { colIndex: 6, format: '0' }                  // Qtd Limite (Inteiro)
            ],
            exportSheetName: 'Produtos Campanha',
            exportFileName: 'produtos_campanha_export.xlsx'
        };

        // Inicializa as funcionalidades da tabela com a configuração
        window.ProductTableUtils.init(config);

    } else {
        console.error("ProductTableUtils não foi carregado.");
    }
});