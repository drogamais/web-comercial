// aplicacao_web_campanhas/static/js/drag_and_drop.js

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".drop-zone__input").forEach((inputElement) => {
        const dropZoneElement = inputElement.closest(".drop-zone");
        const promptElement = dropZoneElement.querySelector(".drop-zone__prompt");

        // Ao clicar na área, aciona o input de arquivo
        dropZoneElement.addEventListener("click", (e) => {
            // Evita abrir o seletor se o clique for no botão de remover
            if (e.target.closest(".drop-zone__remove-button")) {
                return;
            }
            inputElement.click();
        });

        // Atualiza a interface quando um arquivo é escolhido pelo seletor
        inputElement.addEventListener("change", (e) => {
            if (inputElement.files.length) {
                updateThumbnail(dropZoneElement, inputElement.files[0]);
            }
        });

        dropZoneElement.addEventListener("dragover", (e) => {
            e.preventDefault();
            dropZoneElement.classList.add("drop-zone--over");
        });

        ["dragleave", "dragend"].forEach((type) => {
            dropZoneElement.addEventListener(type, (e) => {
                dropZoneElement.classList.remove("drop-zone--over");
            });
        });

        dropZoneElement.addEventListener("drop", (e) => {
            e.preventDefault();
            if (e.dataTransfer.files.length) {
                if (e.dataTransfer.files.length > 1) {
                    alert("Por favor, envie apenas um arquivo por vez. Apenas o primeiro será considerado.");
                }
                const droppedFile = e.dataTransfer.files[0];
                const allowedExtensions = ['xlsx', 'xls'];
                if (allowedExtensions.includes(droppedFile.name.split('.').pop().toLowerCase())) {
                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(droppedFile);
                    inputElement.files = dataTransfer.files;
                    updateThumbnail(dropZoneElement, droppedFile);
                } else {
                    alert("Por favor, envie apenas arquivos Excel (.xlsx, .xls).");
                }
            }
            dropZoneElement.classList.remove("drop-zone--over");
        });

        /**
         * @param {HTMLElement} dropZoneElement
         * @param {File} file
         */
        function updateThumbnail(dropZoneElement, file) {
            let thumbnailElement = dropZoneElement.querySelector(".drop-zone__thumb");
            if (thumbnailElement) thumbnailElement.remove();
            if (promptElement) promptElement.style.display = 'none';

            thumbnailElement = document.createElement("div");
            thumbnailElement.classList.add("drop-zone__thumb");
            
            // --- LÓGICA DO BOTÃO DE REMOVER ---
            const removeButton = document.createElement("div");
            removeButton.innerHTML = "&times;"; // Símbolo "X"
            removeButton.classList.add("drop-zone__remove-button");
            
            removeButton.addEventListener("click", (e) => {
                e.stopPropagation(); // Impede que o evento de clique se propague para a drop-zone
                
                inputElement.value = ""; // Limpa o arquivo do input
                thumbnailElement.remove(); // Remove a miniatura da tela
                if (promptElement) promptElement.style.display = 'block'; // Mostra o texto original novamente
            });
            
            thumbnailElement.appendChild(removeButton);
            // ------------------------------------

            dropZoneElement.appendChild(thumbnailElement);
            thumbnailElement.dataset.label = file.name;
            thumbnailElement.style.backgroundImage = `url('https://e-z.tools/img/icon/ico-excel.svg')`;
        }
    });
});