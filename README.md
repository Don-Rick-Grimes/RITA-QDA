![LibreQDA](http://proyecto.data.cse.edu.uy/attachments/download/672/LibreQDA-logo.png "LibreQDA")
[LibreQDA](https://github.com/tryolabs/libreQDA)
================================================

Copyright (C) 2013 [Tryolabs](http://www.tryolabs.com) 

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see [<http://www.gnu.org/licenses/>](http://www.gnu.org/licenses/).

Instalación
===========

[Virtualenv](https://pypi.python.org/pypi/virtualenv)
------------------------------------------------------
Para mayor comodidad se recomienda utilizar un virtualenv.

1. Instalar Virtualenv: (`sudo apt-get install python-virtualenv` en Debian/Ubuntu).
2. Una vez instalado, crear un Virtualenv: `virtualenv libreqda`.
3. Activar el Virtualenv: `cd libreqda` y luego `source bin/activate`.

Obtener el código
-----------------
Probablemente tengas que instalar git: `sudo apt-get install git`

Luego debes obtener el código de LibreQDA: `git clone https://github.com/tryolabs/libreQDA.git`.


Dependencias
------------
Antes de poder comenzar es necesario instalar algunas dependencias.

1. Instalar `build-essential`: `sudo apt-get install build-essential`.
2. Instalar MySQL: `sudo apt-get install mysql-server libmysqlclient-dev libevent-dev libxml2-dev libxslt1-dev`.
3. El archivo `requirements.txt` contiene una lista de dependencias a instalar. Es posible instalar todas de forma automática con el comando `pip install -r requirements.txt`.

~~Python-docx~~
-----------
~~Para poder extraer el texto de archivos ``docx` es necesario instalar `python-docx`.~~

1. ~~Obtener el código desde su [repositorio en Github](https://github.com/mikemaccana/python-docx): `git clone https://github.com/mikemaccana/python-docx.git`.~~
2. ~~Ir al directorio con el código: `cd python-docx`.~~
3. ~~Instalar con: `python setup.py install`.~~

Configurar y ejecutar
---------------------
1. Crear una base de datos para LibreQDA. El encoding de la base de datos debe ser **UTF-8** para evitar problemas al subir documentos.
  `CREATE DATABASE libreqda CHARACTER SET utf8 COLLATE utf8_general_ci;`
2. Copiar el archivo `local_settings.py.template` que se encuentra junto al código a `local_settings.py`.
3. Abrir el nuevo archivo, `local_settings.py` y editar según sea necesario.
4. Crear la base de datos con django: `python manage.py syncdb`.
5. Ejecutar con: `python manage.py runserver`

Actualizar
----------
Para actualizar LibreQDA simplemente es necesario hacer un pull del repositorio con `git pull` y luego actualizar la base de datos con `python manage.py reset libreqda`.

También es necesario actualziar las dependencias con: `pip install -r requirements.txt`.

NOTA: Los datos son eliminados de la base de datos cuando se hace un `reset`. Es posible utilizar 
[`dumpdata`](https://docs.djangoproject.com/en/dev/ref/django-admin/#dumpdata-appname-appname-appname-model) y 
[`loaddata`](https://docs.djangoproject.com/en/dev/ref/django-admin/#loaddata-fixture-fixture) para exportar e importar datos fácilmente.

FIXME: Ojo, hice un dumpdata y un loaddata y me da error: `Problem installing fixture 'proyectos': dump is not a known serialization format.`

Cómo agregar soporte para otros tipos de archivos
=================================================
Agregar soporte para otros tipos de archivos es relativamente simple. Existen dos archivos a modificar:
* `validators.py`: Contiene código para permitir o no la subida de un tipo de archivo en particular.
* `text_extraction.py`: Contiene el código para extraer el texto de cada uno de los distintos tipos de archivo permitidos.

1. Abrir el archivo `validators.py`.
2. En la tupla `SUPPORTED_FILETYPES` agregar un `string` con el tipo de archivo. Por ejemplo, para archivos Postscript, agregar `'.ps'` a la tupla.
3. Abrir el archivo `tex_extraction.py.
4. Agregar una nueva función con la extensión de archivo como nombre. Por ejemplo, para procesar archivos Postscript, agregar una función llamada `ps`.

  La nueva función va a recibir un solo parámetro, siendo éste el path al nuevo archivo subido. 
  La función debe abrir el archivo y extraer el texto, para finalmente retornar un objeto del tipo `string` con el contenido de archivo. Éste valor será el que se guarde en la base de datos.

TODO
----
Actualmente para determinar el tipo de archivo, LibreQDA se basa en la extensión. La dentificación de tipos de archivos debería realizarse utilizando [`python-magic`](https://github.com/ahupp/python-magic).
