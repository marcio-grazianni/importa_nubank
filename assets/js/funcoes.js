/**
 * Funções genéricas reutilizáveis para o sistema de importação Nubank
 */


/**
 * Foca em um elemento de forma segura, implementando a lógica diretamente
 * Esta função é autossuficiente e não depende de outras funções
 * @param {string} idElemento - ID do elemento a ser focado
 */
function focarElementoOnload(idElemento) {
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function () {
            setTimeout(focarElementoPorId(idElemento), 10);
        });
    } else {
        setTimeout(focarElementoPorId(idElemento), 10);
    }
}

/**
 * Foca em um elemento do DOM por ID após um delay
 * @param {string} idElemento - ID do elemento a ser focado
 */
function focarElementoPorId(idElemento) {
    var elemento = document.getElementById(idElemento);
    setTimeout(function () {
        elemento.focus();
    }, 10);
}

/**
 * Gera um UUID v4
 * @returns {string} UUID no formato xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
 */
function gerarUUID() {
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
        var r = (Math.random() * 16) | 0;
        var v = c == "x" ? r : (r & 0x3) | 0x8;
        return v.toString(16);
    });
}

/**
 * Gera UUID automaticamente para um campo identificador se estiver vazio
 * @param {string} idCampo - ID do campo identificador (padrão: 'id_identificador')
 */
function gerarUUIDAutomatico(idCampo) {
    idCampo = idCampo || "id_identificador";
    var campoIdentificador = document.getElementById(idCampo);
    if (campoIdentificador && !campoIdentificador.value) {
        campoIdentificador.value = gerarUUID();
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
