function eliminarCodigo(nombre,url){
    var r = confirm("¿Realmente desea eliminar el código "+nombre+" del proyecto?");
      if (r == true) {
        //alert(url);
        window.location.replace(url);
        //redirección inicial del botón: href="{% url delete_document pid=project.id did=doc.id %}"
    }
}