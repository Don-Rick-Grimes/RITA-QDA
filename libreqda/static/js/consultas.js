function eliminarConsulta(nombre,url){
    var r = confirm("¿Realmente desea eliminar la consulta "+nombre+" del proyecto?");
      if (r == true) {
        //alert(url);
        window.location.replace(url);
    }
}