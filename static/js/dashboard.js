document.addEventListener('DOMContentLoaded', function() {
    // Seleccionamos todos los títulos de los menús principales
    const titulosMenu = document.querySelectorAll('.titulo-menu');

    titulosMenu.forEach(titulo => {
        titulo.addEventListener('click', function(e) {
            e.preventDefault(); // Evita que el enlace '#' nos lleve al inicio de la página

            // El elemento 'li' padre del título que hemos clickeado
            const itemMenuActual = this.parentElement;
            
            // Si el menú clickeado ya está activo, lo cerramos
            if (itemMenuActual.classList.contains('activo')) {
                itemMenuActual.classList.remove('activo');
            } else {
                // Cerramos cualquier otro menú que esté abierto
                titulosMenu.forEach(otroTitulo => {
                    otroTitulo.parentElement.classList.remove('activo');
                });
                
                // Abrimos el menú que hemos clickeado
                itemMenuActual.classList.add('activo');
            }
        });
    });
});