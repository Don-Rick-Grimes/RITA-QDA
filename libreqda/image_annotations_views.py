from datetime import datetime

import json
from django.shortcuts import get_object_or_404, redirect

from django.contrib.auth.decorators import login_required

from libreqda.utils import JsonResponse
from libreqda.models import ImageInstance, ImageCitation


@login_required
def cit_image_add(request, pid, did):
    i = get_object_or_404(ImageInstance, pk=did)
    if request.method == 'POST':
        serialized = request.POST.get("an")
        citacion = json.loads(serialized)

        add = ImageCitation(image=i,
                            created_by=request.user,
                            creation_date=datetime.now(),
                            modified_date=datetime.now(),
                            comment=citacion["text"],
                            x_coordinate=citacion["shapes"][0]['geometry']['x'],
                            y_coordinate=citacion["shapes"][0]['geometry']['y'],
                            width=citacion["shapes"][0]['geometry']['width'],
                            height=citacion["shapes"][0]['geometry']['height'],
                            serialized=serialized)

        add.save()
        if add.serialized.find('"id":')== -1:
            serializ = add.serialized[:len(add.serialized)-1] + ',"id":'+str(add.id)+'}'
        else:
            serializ = add.serialized[:add.serialized.find(',"id":') - 1] + ',"id":' + str(add.id) + '}'
        add.serialized = serializ
        add.save()
        citations = i.citations.filter(serialized=serializ)
        payload = {"datos": []}
        for cit in citations:
            payload["datos"].append({"serial": cit.serialized,"id": cit.id})
        return JsonResponse(payload)
    else:
        return redirect('http://localhost:8000/project/' + str(pid) + '/images/' + str(did) + '/')


@login_required
def cit_image_update(request, pid, did):

    if request.method == 'POST':
        serialized = request.POST.get("an")
        citacion = json.loads(serialized)
        id = citacion["id"]
        update = ImageCitation.objects.get(pk=id)
        update.modified_date = datetime.now()
        update.comment = citacion["text"]
        update.serialized = serialized
        update.save()
        return JsonResponse({"success":True})

    else:
        return redirect('http://localhost:8000/project/' + str(pid) + '/images/' + str(did) + '/')


@login_required
def cit_image_del(request, pid, did):

    if request.method == 'POST':
        serialized = request.POST.get("an")
        citacion = json.loads(serialized)
        id = citacion["id"]
        deleted = ImageCitation.objects.get(pk=id)
        deleted.delete()
        return JsonResponse({"success":True})
    else:
        return redirect('view_image', pid=pid, did=did)