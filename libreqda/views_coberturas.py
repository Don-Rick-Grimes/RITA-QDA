from datetime import datetime

from django.shortcuts import render, get_object_or_404

from django.contrib.auth.decorators import login_required

from django.db.models import Count


import numpy as np

import json
from libreqda.utils import JsonResponse
from libreqda.models import Project, Code, UserProjectPermission, ImageCitation, Image, ImageInstance, Coberturas

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from operator import attrgetter


@login_required
def sugerencia(request, pid, did):
    if request.method == 'POST':
        cid = request.POST.get("cid")
        p = get_object_or_404(Project, pk=pid)
        cit = get_object_or_404(ImageCitation, pk=cid)
        selector = request.POST.get("selector")
        name = request.POST.get("name")
        sugerencia = Code.objects.filter(name=name)
        if sugerencia.count() <= 0:
            if selector == 'arbol':
                nombre = name
                peso = 55
                tecnicolor = 's'
                comentario = "Cobertura de arboles"
            elif selector == 'cesped':
                nombre = name
                peso = 45
                tecnicolor = 'd'
                comentario = "Cobertura de cesped"
            elif selector == 'suelo':
                nombre = name
                peso = 20
                tecnicolor = 'w'
                comentario = "Cobertura de suelo descubierto"
            elif selector == 'agua':
                nombre = name
                peso = 15
                tecnicolor = 'i'
                comentario = "Cobertura de cuerpos de agua"
            else:
                return JsonResponse({"success": False})
            c = Code(project=p,
                     name=nombre,
                     weight=peso,
                     created_by=request.user,
                     color=tecnicolor,
                     comment=comentario,
                     modified_date=datetime.now(),
                     creation_date=datetime.now())
            c.save()
            cit.codes.add(c)
        else:
            c = Code.objects.get(name=name)
            cit.codes.add(c)
        response_data = {'success': True}
        response_data['cid'] = cid
        response_data['codes_str'] = cit.codes_str()
        response_data['codes_color'] = cit.html_color()
        response_data['top'] = cit.y_coordinate
        response_data['left'] = cit.x_coordinate
        response_data['width'] = cit.width
        return JsonResponse(response_data)
    else:
        try:
            coverage = Coberturas.objects.get(id_image=did)
            datos = {"success": True,
                    "codigos": coverage.coberturas,
                    "x": coverage.parte_x,
                    "y": coverage.parte_y}
            return JsonResponse(datos)

        except:
            datos = {"success": False}
            return JsonResponse(datos)


@login_required
def similar(request, pid, did, template='view_similar_image.html'):
    coverage = Coberturas.objects.get(id_image=did)
    coverages = Coberturas.objects.exclude(id_image=did)
    image_duplicates = Image.objects.values('file').annotate(file_count=Count('file')).filter(file_count__gt=1)
    excludes = []
    data = []
    if image_duplicates.exists():
        for duplicate in image_duplicates:
            data.extend(Image.objects.filter(file=duplicate['file']).values('id', 'file'))
        id_url = {}
        for dat in data:
            id_url[str(dat['id'])] = dat['file']
        instances = ImageInstance.objects.filter(project_id=pid).values('image_id')
        for id in instances:
            iid = str(id['image_id'])
            try:
                id_url[iid]
                excludes.append(id_url[iid])
            except:
                print("no esta repetido")
    payload = {"coverage": []}
    vector_a = np.array([coverage.arbol, coverage.cesped, coverage.suelo, coverage.agua], dtype=float)
    for cover in coverages:
        vector_b = np.array([cover.arbol, cover.cesped, cover.suelo, cover.agua], dtype=float)
        #euclideo = (np.dot((vector_a-vector_b), (vector_a-vector_b)))**0.5
        #sim_cos = np.dot(vector_a, vector_b)/((np.dot(vector_a, vector_a)*np.dot(vector_b, vector_b))**0.5)
        #canberra = sum(np.divide(abs(vector_a - vector_b), (abs(vector_a) + abs(vector_b))))
        manhattan = sum(abs(vector_a - vector_b))
        #manhattanA = abs(coverage.arbol-cover.arbol)
        #manhattanB = abs(coverage.cesped-cover.cesped)
        #manhattanC = abs(coverage.suelo-cover.suelo)
        #manhattanD = abs(coverage.agua-cover.agua)
        if float(manhattan) < 0.36 and int(cover.id_image.project_id) != int(pid): #si la imagen supera umbral y no pertenece al mismo proyecto
            if cover.id_image.image.share: #si la imagen esta compartida con otros proyectos
                if excludes.count(cover.id_image.image.file) == 0: #si la imagen no se repite en otro proyecto
                    cover.signature = manhattan
                    payload["coverage"].append(cover)
    payload["coverage"].sort(key=attrgetter('signature'), reverse=False)
    paginator = Paginator(payload["coverage"], 6)
    page = request.GET.get('page')
    try:
        images = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        images = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        images = paginator.page(paginator.num_pages)
    page_range = paginator.page_range
    page_range = map(str, page_range)
    return render(request, template, {"images": images,
                                      "page_range": page_range,
                                      "pid": pid,
                                      "did": did})


@login_required
def add_image_to_project(request, pid, did):
    p = get_object_or_404(Project, pk=pid)
    if request.method == 'POST':
        id = request.POST.get("id")
        i = get_object_or_404(Image, pk=id)
        image = Image(name=i.name,
                      comment=i.comment,
                      uploaded_by=request.user,
                      file=i.file,
                      type=i.type,
                      share=False)
        image.save()
        img_instance = ImageInstance(name=i.name,
                                     project=p,
                                     comment=i.comment,
                                     image=image,
                                     type=i.type,
                                     uploaded_by=request.user)
        img_instance.save()
        im = ImageInstance.objects.get(image=id)
        c = Coberturas.objects.get(id_image=im.id)

        cobertura = Coberturas(id_image=img_instance,
                               coberturas=c.coberturas,
                               parte_x=c.parte_x,
                               parte_y=c.parte_y,
                               arbol=c.arbol,
                               cesped=c.cesped,
                               suelo=c.suelo,
                               agua=c.agua)
        cobertura.save()
    return JsonResponse({"success": True})


