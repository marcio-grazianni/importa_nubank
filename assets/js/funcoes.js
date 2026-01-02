/**
 * Funções genéricas reutilizáveis para o sistema de importação Nubank
 */

/**
 * Foca em um elemento de forma segura
 * @param {string} idElemento - ID do elemento a ser focado
 */
function focarElementoOnload(idElemento) {
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function () {
            setTimeout(function () {
                focarElementoPorId(idElemento);
            }, 10);
        });
    } else {
        setTimeout(function () {
            focarElementoPorId(idElemento);
        }, 10);
    }
}

/**
 * Foca em um elemento do DOM por ID
 * @param {string} idElemento - ID do elemento a ser focado
 */
function focarElementoPorId(idElemento) {
    var elemento = document.getElementById(idElemento);
    if (elemento) {
        setTimeout(function () {
            elemento.focus();
        }, 10);
    }
}

/**
 * Destaca o label de um input de arquivo (fallback quando o foco não é permitido)
 * @param {string} idInput - ID do input de arquivo
 * @param {string} cor - Cor para destacar o label (padrão: '#007bff')
 */
function destacarLabelArquivo(idInput, cor) {
    idInput = idInput || "csv_file";
    cor = cor || "#007bff";
    var fileInput = document.getElementById(idInput);
    if (fileInput) {
        try {
            fileInput.focus();
        } catch (e) {
            var label = document.querySelector('label[for="' + idInput + '"]');
            if (label) {
                label.style.color = cor;
            }
        }
    }
}
