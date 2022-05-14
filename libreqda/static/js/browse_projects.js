$(document).ready(function(){
	var url = window.location.href;
	var pos = url.indexOf("#document");
	if(pos>0){
		//Para mostrar la lista de documentos
		$('ul.nav-tabs li:nth-child(1)').attr('class',' ');
		$('ul.nav-tabs li:nth-child(2)').attr('class','active');
		$('div.tab-content div:nth-child(1)').attr('class','tab-pane tight-tab-content');
		$('div.tab-content div:nth-child(2)').attr('class','tab-pane tight-tab-content active');
	}
})
function eliminarProyecto() {
	var url = window.location.href;
    var r = confirm("¿Realmente desea eliminar el proyecto?");
    if (r == true) {
        window.location.replace(url+"/delete");
    }
}
function eliminarDocumento(nombre,url){
	var r = confirm("¿Realmente desea eliminar el documento "+nombre+"?");
    if (r == true) {
    	//alert(url);
        window.location.replace(url);
        //redirección inicial del botón: href="{% url delete_document pid=project.id did=doc.id %}"
    }
}
function eliminarUsuario(nombre,url){
	var r = confirm("¿Realmente desea eliminar usuario "+nombre+" del proyecto?");
    if (r == true) {
    	//alert(url);
        window.location.replace(url);
        //redirección inicial del botón: href="{% url delete_document pid=project.id did=doc.id %}"
    }
}