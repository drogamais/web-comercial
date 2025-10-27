// static/js/produtosTabloidePage.js

document.addEventListener('DOMContentLoaded', function() {
    if (window.ProductTableUtils && window.ProductTableUtils.init) {

        // --- Configuração Específica da Página de Produtos de Tabloide ---
        const config = {
            tableSelector: '#form-edit-delete table', // Seletor da tabela (mesmo ID, ok)
            precoNormalSelector: 'input[name*="preco_normal_"]',
            precoDesconto1Selector: 'input[name*="preco_desconto_"]', // Corresponde ao Preço Geral
            precoDesconto2Selector: 'input[name*="preco_desconto_cliente_"]', // Corresponde ao Preço Cliente+
            // IMPORTANTE: Adicionar a rota no backend tabloide_routes.py!
            validateGtinUrl: '/tabloide/{id}/produtos/validar_gtins', // URL da API (com placeholder)
            exportHeaders: [ // Cabeçalhos para o Excel
                "Codigo Barras", "Descricao", "Laboratorio", "Tipo Preco",
                "Preco Normal", "Preco Geral", "Preco Cliente+", "Preço APP", "Tipo Regra"
            ],
             exportValueSelectors: [ // Seletores na ordem dos cabeçalhos
                { selector: 'input[name*="codigo_barras_"]', isNumeric: false },
                { selector: 'input[name*="descricao_"]', isNumeric: false },
                { selector: 'input[name*="laboratorio_"]', isNumeric: false },
                { selector: 'input[name*="tipo_preco_"]', isNumeric: false },
                { selector: 'input[name*="preco_normal_"]', isNumeric: true, isInteger: false },
                { selector: 'input[name*="preco_desconto_"]', isNumeric: true, isInteger: false }, // Preço Geral
                { selector: 'input[name*="preco_desconto_cliente_"]', isNumeric: true, isInteger: false }, // Preço Cliente+
                { selector: 'input[name*="preco_app_"]', isNumeric: true, isInteger: false }, // Preço App
                { selector: 'input[name*="tipo_regra_"]', isNumeric: false }
            ],
             exportFormatConfig: [ // Formatação para colunas numéricas (índice baseado em exportHeaders)
                 { colIndex: 4, format: '#,##0.00' },          // Preco Normal
                 { colIndex: 5, format: '#,##0.00' },          // Preco Geral
                 { colIndex: 6, format: '#,##0.00' },          // Preco Cliente+
                 { colIndex: 7, format: '#,##0.00' }           // Preco App
            ],
            exportSheetName: 'Produtos Tabloide',
            exportFileName: 'produtos_tabloide_export.xlsx'
        };

        // Inicializa as funcionalidades da tabela com a configuração
        window.ProductTableUtils.init(config);

    } else {
        console.error("ProductTableUtils não foi carregado.");
    }
});