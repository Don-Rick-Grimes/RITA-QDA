function eliminarCategoria(nombre,url){
    var r = confirm("¿Realmente desea eliminar la categoría "+nombre+" del proyecto?");
      if (r == true) {
        window.location.replace(url);
    }
}