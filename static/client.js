document.addEventListener('DOMContentLoaded', () => {
    // Inicializa la conexión con el servidor Flask
    const socket = io();

    // Referencias a los elementos HTML de nuestra terminal
    const terminalOutput = document.getElementById('output');
    const terminalInput = document.getElementById('input');
    const promptLabel = document.getElementById('prompt-label');

    /**
     * Añade un mensaje a la pantalla de la terminal y hace scroll hacia abajo.
     * @param {string} message - El texto a imprimir.
     */
    function printToTerminal(message) {
        // Reemplazamos saltos de línea con <br> para que HTML los renderice
        terminalOutput.innerHTML += message.replace(/\n/g, '<br>');
        // Mantenemos la vista siempre al final del contenido
        terminalOutput.parentElement.scrollTop = terminalOutput.parentElement.scrollHeight;
    }

    // --- MANEJADORES DE EVENTOS DEL SERVIDOR ---

    // 1. El servidor nos envía texto para mostrar en la terminal
    socket.on('terminal_output', function(msg) {
        printToTerminal(msg.data);
    });

    // 2. El servidor nos pide que el usuario introduzca algo
    socket.on('request_input', function(msg) {
        promptLabel.innerHTML = msg.prompt; // Actualizamos el texto del prompt
        terminalInput.disabled = false;    // Habilitamos el campo de texto
        terminalInput.focus();             // Ponemos el cursor en él
    });

    // --- MANEJADORES DE EVENTOS DEL USUARIO ---

    // 3. El usuario presiona una tecla en el campo de texto
    terminalInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            const command = terminalInput.value;
            
            // Mostramos en la pantalla lo que el usuario acaba de escribir
            printToTerminal(`${promptLabel.textContent}${command}\n`);

            // Limpiamos y deshabilitamos el input mientras esperamos la respuesta del servidor
            terminalInput.value = '';
            terminalInput.disabled = true;
            promptLabel.textContent = '';

            // Enviamos el comando al servidor
            socket.emit('terminal_input', { data: command });
        }
    });

    // --- MANEJO DE LA CONEXIÓN ---

    socket.on('connect', function() {
        console.log('Conectado al servidor con SID:', socket.id);
    });

    socket.on('disconnect', function() {
        printToTerminal('\n[CONEXIÓN PERDIDA CON EL SERVIDOR]\n');
        terminalInput.disabled = true;
        promptLabel.textContent = '';
    });
});