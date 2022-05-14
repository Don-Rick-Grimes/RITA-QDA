# -*- coding: utf-8 -*-
from os.path import splitext
from datetime import datetime

from django.http import Http404
from django.template import RequestContext
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

import libreqda.text_extraction
from libreqda.utils import JsonResponse
from libreqda.forms import AddCodeToAnnotation, AddUserToProjectForm, \
    AddCodeToCitationForm, AnnotationForm, BooleanQueryForm, CategoryForm, \
    CodeForm, ProjectForm, SetQueryForm, UploadDocumentForm, UploadImageForm, \
    ProximityQueryForm, AddAnnotationToCitationForm, SemanticQueryForm

from libreqda.models import Category, Annotation, BooleanQuery, Document, Image, \
    DocumentInstance, ImageInstance, Project, ProximityQuery, SemanticQuery, SetQuery, \
    Citation, ImageCitation, Code, UserProjectPermission, Coberturas

from libreqda.clasificacion import Clasificacion_rural, Clasificacion_cobertura
import os
import numpy as np

## Base

@login_required
def home(request):
    return redirect('browse_projects')


## about

def about(request, template='about.html'):
    return render(request, template, {})


## proyecto

@login_required
def view_project(request,pid,template='view_project.html'):
    p = get_object_or_404(Project, pk=pid)
    if p.owner == request.user:
        user = request.user
        user_perms = UserProjectPermission.objects.filter(user=user)
        projects = Project.objects.filter(permissions__in=user_perms, pk=pid)
        allProjects = Project.objects.filter(permissions__in=user_perms)
        return render(request, template, {'projects': projects,
                                          'allProjects': allProjects})
    else:
        raise Http404

## Projects

@login_required
def browse_projects(request, template='browse_projects.html'):
    user = request.user
    user_perms = UserProjectPermission.objects.filter(user=user)
    projects = Project.objects.filter(permissions__in=user_perms)

    return render(request, template, {'projects': projects})


@login_required
def new_project(request, template='new_project.html'):
    if request.method == 'POST':
        p = Project()
        form = ProjectForm(request.POST, instance=p)

        if form.is_valid():
            # Create project and set owner
            p.owner = request.user
            p.save()

            # Create an administrative privilege and assign it
            perm = UserProjectPermission()
            perm.creation_date = datetime.now()
            perm.modified_date = datetime.now()
            perm.user = p.owner
            perm.project = p
            perm.permissions = 'a'  # admin
            perm.save()

            return redirect('browse_projects')
    else:
        form = ProjectForm()

    form_action = reverse('new_project')
    user = request.user
    user_perms = UserProjectPermission.objects.filter(user=user)
    allProjects = Project.objects.filter(permissions__in=user_perms)
    return render(request,
                  template,
                  {'project_form': form,
                   'form_action': form_action,
                   'back_url': reverse('browse_projects'),
                   'allProjects': allProjects})


@login_required
def add_user_to_project(request, pid, template='modal.html'):
    if request.method == 'POST':
        form = AddUserToProjectForm(request.POST)
        p = get_object_or_404(Project, pk=pid)

        if form.is_valid():
            for u in form.cleaned_data['users']:
                perm = UserProjectPermission()
                perm.user = u
                perm.project = p
                perm.permissions = 'g'
                perm.save()
            # se actualiza la fecha de modificación 14-06-2014
            p.modified_date = datetime.now()
            p.save()
            # All OK, redirect to projects home
            response_data = {'redirect': reverse('browse_projects')}
            return JsonResponse(response_data)
    else:
        p = get_object_or_404(Project, pk=pid)
        form = AddUserToProjectForm()

    form_action = reverse('add_user_to_project', kwargs={'pid': pid})
    form.fields['users'].queryset = User.objects.exclude(
                                        permissions__in=p.permissions.all())
    response_dict = {
                     'form': form,
                     'form_action': form_action,
                     'form_header': _('Asignar usuarios al proyecto'),
                    }
    html_response = render_to_string(
                        template, response_dict, RequestContext(request))

    response_data = {'html': html_response}
    return JsonResponse(response_data)


@login_required
def remove_user_from_project(request, pid, uid):
    p = get_object_or_404(Project, pk=pid)
    u = get_object_or_404(User, pk=uid)
    admin_perm = UserProjectPermission.objects.filter(
                        user=request.user, project=p, permissions='a')

    if u == p.owner:
        raise Exception(_(
                'No se puede remover del projecto a su propietario.'))

    if p.owner == request.user or admin_perm.exists():
        perm = UserProjectPermission.objects.get(user=u, project=p)
        perm.delete()
        # se actualiza la fecha de modificación 14-06-2014
        p.modified_date = datetime.now()
        p.save()
    else:
        raise Exception(_('Permisos insuficientes.'))

    return redirect('browse_projects')


@login_required
def delete_project(request, pid):
    p = get_object_or_404(Project, pk=pid)
    if p.owner == request.user:
        p.delete()
    else:
        raise Http404

    return redirect('browse_projects')


@login_required
def copy_project(request, pid, template='copy_project.html'):
    p = get_object_or_404(Project, pk=pid)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=p)

        if form.is_valid():
            p.owner = request.user
            p.pk = None
            p.save()

            return redirect('browse_projects')
    else:
        form = ProjectForm()

    form_action = reverse('copy_project',
                          args=(pid,))
    return render(request,
                  template,
                  {'project_form': form,
                   'form_action': form_action,
                   'back_url': reverse('browse_projects')})


## Documents

@login_required
def view_document(request, pid, did, template='view_document.html'):
    p = get_object_or_404(Project, pk=pid)
    d = get_object_or_404(DocumentInstance, pk=did)

    texts = {
        'add_code': _(u'Asignar códigos'),
        'add_annotation': _(u'Asignar anotación'),
        'view_details': _('Ver detalles'),
    }

    return render(request,
                  template,
                  {'project': p,
                   'document': d,
                   'citations': d.citations.order_by('start'),
                   'texts': texts})


#Uncomment this to enable file selection instead of uploading a new file
#@login_required
#def new_document(request, pid, template='new_document.html'):
#    p = get_object_or_404(Project, pk=pid)
#
#    if request.method == 'POST':
#        form = NewDocumentForm(request.POST)
#        if form.is_valid():
#            name = form.cleaned_data['name']
#            comment = form.cleaned_data['comment']
#            document_id = form.cleaned_data['document']
#            document = get_object_or_404(Document, pk=document_id)
#
#            doc_instance = DocumentInstance(name=name,
#                                            project=p,
#                                            comment=comment,
#                                            document=document,
#                                            type=document.type,
#                                            uploaded_by=request.user)
#            doc_instance.save()
#            return redirect('browse_projects')
#    else:
#        form = NewDocumentForm()
#
#    return render(request,
#              template,
#              {'project': p,
#               'documents': Document.objects.all(),
#               'form': form})


def extract_text(path, extension):
    return getattr(libreqda.text_extraction, extension.lower()[1:])(path)


@login_required
def upload_document(request, pid, template='upload_document.html'):
    p = get_object_or_404(Project, pk=pid)

    if request.method == 'POST':
        form = UploadDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data['name']
            comment = form.cleaned_data['comment']
            document_file = request.FILES['document']
            document_file.name = document_file.name.replace(" ","_")
            document = Document(name=name,
                                comment=comment,
                                uploaded_by=request.user,
                                file=document_file,
                                type=splitext(document_file.name)[1])
            document.save()

            doc_instance = DocumentInstance(name=name,
                                            project=p,
                                            comment=comment,
                                            document=document,
                                            type=document.type,
                                            uploaded_by=request.user)
            doc_instance.save()
            document.file.close()
            # se actualiza la fecha de modificación 14-06-2014
            p.modified_date = datetime.now()
            p.save()
            try:
                text = extract_text(document.file.path,
                                    document.type)
                document.text = text.replace("&#160;"," ")
                document.save()
                doc_instance.save()
            except:
                doc_instance.delete()
                document.file.delete()
                document.delete()

                return render(request,
                    'error.html',
                    {'title': _(u'¡Oops!'),
                     'message': _('Hubo un error al agregar el documento.'),
                     'backtext': _('Agregar otro documento.'),
                     'backlink': reverse('upload_document', args=(pid,))
                    })
                #   redirect('browse_projects') -- 14/06/2016  09:22
            return redirect('/project/'+pid+"#document")
    else:
        form = UploadDocumentForm()
    # back_url = reverse('browse_projects') -- 14/06/2016  09:22

    back_url = reverse('view_project', args=(pid,))
    form_action = reverse('upload_document', args=(pid,))
    return render(request,
                  template,
                  {'project': p,
                   'documents': Document.objects.all(),
                   'form': form,
                   'form_action': form_action,
                   'back_url': back_url})


@login_required
def delete_document(request, pid, did):
    p = get_object_or_404(Project, pk=pid)
    d = get_object_or_404(DocumentInstance, pk=did)

    if p.owner == request.user:
        d.document.delete()
        d.delete()
        # se actualiza la fecha de modificación 14-06-2014
        p.modified_date = datetime.now()
        p.save()
    else:
        raise Http404

    return redirect('browse_projects')


## Codes

@login_required
def browse_codes(request, pid, template='browse_codes.html'):
    p = get_object_or_404(Project, pk=pid)

    return render(request,
              template,
              {'project': p})

@login_required
def browse_codes_from_document(request, pid, template='browse_codes_from_document.html'):
    p = get_object_or_404(Project, pk=pid)

    response_dict = {'project': p}
    html_response = render_to_string(
                        template, response_dict, RequestContext(request))

    response_data = {'html': html_response}
    return JsonResponse(response_data)

@login_required
def browse_category_codes(request,pid,cid,template='browse_category_codes.html'):
    #se implementa la función de mostrar los códigos de una categoría en particular
    p = get_object_or_404(Project, pk=pid)
    category_name = Category.objects.get(pk=cid).name
    codes = Category.objects.get(pk=cid).codes.all()
    return render(request,
              template,
              {'codes': codes,
              'category_name': category_name,
              'project': p})

@login_required
def new_code(request, pid, template='new_code.html'):
    p = get_object_or_404(Project, pk=pid)

    back_or_success = reverse('browse_codes', args=(pid,))

    # Create queryset to filter possible parent codes
    choices = Code.objects.filter(project=pid)

    if request.method == 'POST':
        c = Code()
        form = CodeForm(request.POST, instance=c)
        # Modify form's queryset for validation
        form.fields['parent_codes'].queryset = choices

        if form.is_valid():
            c.created_by = request.user
            c.project = p
            c.save()

            for parent in form.cleaned_data['parent_codes']:
                c.parent_codes.add(parent)
            c.save()
            # se actualiza la fecha de modificación 14-06-2014
            p.modified_date = datetime.now()
            p.save()
            return redirect(back_or_success)
    else:
        form = CodeForm()
        # Only display project's codes
        form.fields['parent_codes'].queryset = choices

    form_action = reverse('new_code', args=(pid,))
    return render(request,
              template,
              {'form': form,
               'form_action': form_action,
               'back_url': back_or_success})

@login_required
def edit_code(request, pid, cid,template='new_code.html'):
    p = get_object_or_404(Project, pk=pid)
    c = get_object_or_404(Code, pk=cid)
    back_or_success = reverse('browse_codes', args=(pid,))
    # Create queryset to filter possible parent codes
    choices = Code.objects.filter(project=pid).exclude(id =cid)
    if request.method == 'POST':
        #c = Code()
        form = CodeForm(request.POST, instance=c)
        # Modify form's queryset for validation
        form.fields['parent_codes'].queryset = choices
        c.parent_codes.clear()
        if form.is_valid():
            c.save()
            #se debe eliminar
            for parent in form.cleaned_data['parent_codes']:
                c.parent_codes.add(parent)
            c.save()
            # se actualiza la fecha de modificación 14-06-2014
            p.modified_date = datetime.now()
            p.save()
            return redirect(back_or_success)
    else:
        form = CodeForm()
        # Only display project's codes
        form.fields['parent_codes'].queryset = choices
    form_action = reverse('edit_code', args=(pid,cid,))
    return render(request,
              template,
              {'form': form,
               'form_action': form_action,
               'back_url': back_or_success,
               'code':c})

@login_required
def delete_code(request, pid, cid):
    p = get_object_or_404(Project, pk=pid)
    c = get_object_or_404(Code, pk=cid)

    if c.project == p and c.created_by == request.user:
        c.delete()
        # se actualiza la fecha de modificación 14-06-2014
        p.modified_date = datetime.now()
        p.save()
    else:
        raise Http404

    return redirect('browse_codes', pid=pid)


## Annotations

@login_required
def browse_annotations(request, pid, template='browse_annotations.html'):
    p = get_object_or_404(Project, pk=pid)

    return render(request,
              template,
              {'project': p})


@login_required
def new_annotation(request, pid, template='new_annotation.html'):
    p = get_object_or_404(Project, pk=pid)

    back_or_success = reverse('browse_annotations', args=(pid,))

    if request.method == 'POST':
        a = Annotation()
        form = AnnotationForm(request.POST, instance=a)
        if form.is_valid():
            a.created_by = request.user
            a.project = p
            a.save()
            # se actualiza la fecha de modificación 14-06-2014
            p.modified_date = datetime.now()
            p.save()

            return redirect(back_or_success)
    else:
        form = AnnotationForm()

    form_action = reverse('new_annotation', args=(pid,))
    return render(request,
              template,
              {'form': form,
               'form_action': form_action,
               'back_url': back_or_success})


@login_required
def delete_annotation(request, pid, aid):
    p = get_object_or_404(Project, pk=pid)
    a = get_object_or_404(Annotation, pk=pid)

    if request.user in p.admin_users():
        a.delete()
        # se actualiza la fecha de modificación 14-06-2014
        p.modified_date = datetime.now()
        p.save()
    else:
        raise Http404

    return reverse('browse_annotations', args=(pid,))


@login_required
def add_code_to_annotation(request, pid, aid, template='modal.html'):
    p = get_object_or_404(Project, pk=pid)
    a = get_object_or_404(Annotation, pk=aid)

    if a.project != p:
        raise Http404

    if request.method == 'POST':
        form = AddCodeToAnnotation(request.POST)
        form.fields['codes'].queryset = p.codes.all()

        if form.is_valid():
            for code in form.cleaned_data['codes']:
                a.codes.add(code)
            a.save()
            response_data = {'redirect': reverse('browse_annotations',
                                                 args=(pid,))}
            # se actualiza la fecha de modificación 14-06-2014
            p.modified_date = datetime.now()
            p.save()
            return JsonResponse(response_data)
    else:
        form = AddCodeToAnnotation()

    form_action = reverse('add_code_to_annotation', args=(pid, aid))
    form.fields['codes'].queryset = p.codes.exclude(
                                        id__in=a.codes.all().values('id'))

    response_dict = {
                     'form': form,
                     'form_action': form_action,
                     'form_header': _(u'Asignar códigos a la anotación'),
                    }
    html_response = render_to_string(
                        template, response_dict, RequestContext(request))

    response_data = {'html': html_response}
    return JsonResponse(response_data)


@login_required
def remove_code_from_annotation(request, pid, aid, cid):
    p = get_object_or_404(Project, pk=pid)
    a = get_object_or_404(Annotation, pk=aid)
    c = get_object_or_404(Code, pk=cid)

    if c not in a.codes.all():
        raise Http404

    if request.user in p.admin_users():
        a.codes.remove(c)
        a.save()
        # se actualiza la fecha de modificación 14-06-2014
        p.modified_date = datetime.now()
        p.save()
    else:
        raise Http404

    return redirect('browse_annotations', pid=pid)


## Categories

@login_required
def browse_categories(request, pid, template='browse_categories.html'):
    p = get_object_or_404(Project, pk=pid)

    return render(request,
                  template,
                  {'project': p})


@login_required
def new_category(request, pid, template='new_category.html'):
    p = get_object_or_404(Project, pk=pid)

    back_or_success = reverse('browse_categories', args=(pid,))
    #se cargan los códigos que pertenecen a este proyecto
    choices = Code.objects.filter(project=pid)
    if request.method == 'POST':
        c = Category()
        form = CategoryForm(request.POST, instance=c)
        if form.is_valid():
            c.created_by = request.user
            c.project = p
            c.save()
            # se asocian los códigos a la categoría 14-09-2016
            for code in form.cleaned_data['codes']:
                c.codes.add(code)
            c.save()
            # se actualiza la fecha de modificación 14-06-2014
            p.modified_date = datetime.now()
            p.save()
            return redirect(back_or_success)
    else:
        form = CategoryForm()
        # Only display project's codes
        form.fields['codes'].queryset = choices


    form_action = reverse('new_category', args=(pid,))
    return render(request,
                  template,
                  {'form': form,
                   'form_action': form_action,
                   'back_url': back_or_success})

@login_required
def edit_category(request, pid, cid, template='new_category.html'):
    p = get_object_or_404(Project, pk=pid)
    c = get_object_or_404(Category, pk=cid)
    back_or_success = reverse('browse_categories', args=(pid,))
    #se cargan los códigos que pertenecen a este proyecto
    choices = Code.objects.filter(project=pid)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=c)
        if form.is_valid():
            c.codes.clear()
            # se asocian los códigos a la categoría 14-09-2016
            for code in form.cleaned_data['codes']:
                c.codes.add(code)
            c.save()
            # se actualiza la fecha de modificación 14-06-2014
            p.modified_date = datetime.now()
            p.save()
            return redirect(back_or_success)
    else:
        form = CategoryForm()
        # Only display project's codes
        form.fields['codes'].queryset = choices


    form_action = reverse('edit_category', args=(pid,cid,))
    return render(request,
                  template,
                  {'form': form,
                   'form_action': form_action,
                   'back_url': back_or_success,
                   'category':c})

@login_required
def delete_category(request, pid, cid):
    p = get_object_or_404(Project, pk=pid)
    c = get_object_or_404(Category, pk=cid)

    if c.project == p and c.created_by == request.user:
        c.delete()
        # se actualiza la fecha de modificación 14-06-2014
        p.modified_date = datetime.now()
        p.save()
    else:
        raise Http404

    return redirect('browse_categories', pid=pid)


## Citations

@login_required
def add_code_to_citation(request, pid, cid, template='modal.html'):
    if request.method == 'POST':
        form = AddCodeToCitationForm(request.POST)
        p = get_object_or_404(Project, pk=pid)
        cit = get_object_or_404(Citation, pk=cid)

        if form.is_valid():
            response_data = {'success': True}
            for code in form.cleaned_data['codes']:
                if cit.codes.filter(pk=code.pk).exists():
                    response_data = {'error': _('Code already in project')}
                    break
                cit.codes.add(code)
            response_data['cid'] = cid
            response_data['codes_str'] = cit.codes_str()
            # se actualiza la fecha de modificación 14-06-2014
            p.modified_date = datetime.now()
            p.save()
            return JsonResponse(response_data)
    else:
        p = get_object_or_404(Project, pk=pid)
        cit = get_object_or_404(Citation, pk=cid)
        form = AddCodeToCitationForm()

    form_action = reverse('add_code_to_citation',
                          kwargs={'pid': pid, 'cid': cid})
    available_codes = Code.objects.filter(project=p).exclude(
                                                    pk__in=cit.codes.all())
    form.fields['codes'].queryset = available_codes
    response_dict = {
                     'form': form,
                     'form_action': form_action,
                     'form_header': _(u'Asignar códigos a la cita'),
                    }
    html_response = render_to_string(
                        template, response_dict, RequestContext(request))

    response_data = {'html': html_response}
    return JsonResponse(response_data)


@login_required
def remove_code_from_citation(request, pid, citid, codeid):
    cit = get_object_or_404(Citation, pk=citid)
    code = get_object_or_404(Code, pk=codeid)

    if code not in cit.codes.all():
        raise Http404

    cit.codes.remove(code)
    cit.save()
    # se actualiza la fecha de modificación 15-06-2014
    p.modified_date = datetime.now()
    p.save()
    return redirect('view_document', pid=pid, did=cit.document.pk)


@login_required
def add_annotation_to_citation(request, pid, cid, template='modal.html'):
    if request.method == 'POST':
        form = AddAnnotationToCitationForm(request.POST)
        p = get_object_or_404(Project, pk=pid)
        cit = get_object_or_404(Citation, pk=cid)

        if form.is_valid():
            response_data = {'success': True}
            for ann in form.cleaned_data['annotations']:
                if cit.annotations.filter(pk=ann.pk).exists():
                    response_data = {
                        'error': _('Annotation already in project')
                    }
                    break
                cit.annotations.add(ann)
                # se actualiza la fecha de modificación 14-06-2014
                p.modified_date = datetime.now()
                p.save()
            return JsonResponse(response_data)
    else:
        p = get_object_or_404(Project, pk=pid)
        cit = get_object_or_404(Citation, pk=cid)
        form = AddAnnotationToCitationForm()

    form_action = reverse('add_annotation_to_citation',
                          kwargs={'pid': pid, 'cid': cid})
    available_anns = Annotation.objects.filter(project=p).exclude(
                                                pk__in=cit.annotations.all())
    form.fields['annotations'].queryset = available_anns
    response_dict = {
                     'form': form,
                     'form_action': form_action,
                     'form_header': _('Asignar anotaciones a la cita'),
                    }
    html_response = render_to_string(
                        template, response_dict, RequestContext(request))

    response_data = {'html': html_response}
    return JsonResponse(response_data)


@login_required
def remove_annotation_from_citation(request, pid, citid, aid):
    c = get_object_or_404(Citation, pk=citid)
    a = get_object_or_404(Annotation, pk=aid)

    if a not in c.annotations.all():
        raise Http404

    c.annotations.remove(a)
    c.save()
    # se actualiza la fecha de modificación 14-06-2014
    p.modified_date = datetime.now()
    p.save()
    return redirect('view_document', pid=pid, did=c.document.pk)


@login_required
def citation_details(request, pid, cid, template='citation_details.html'):
    p = get_object_or_404(Project, pk=pid)
    cit = get_object_or_404(Citation, pk=cid)
    response_dict = {
                     'project': p,
                     'citation': cit,
                     'form_header': _('Detalles de la cita'),
                    }
    html_response = render_to_string(
                        template, response_dict, RequestContext(request))

    response_data = {'html': html_response}
    return JsonResponse(response_data)


## Queries

@login_required
def browse_queries(request, pid, template='browse_queries.html'):
    p = get_object_or_404(Project, pk=pid)

    return render(request, template, {'project': p})


@login_required
def new_boolean_query(request, pid, template='new_boolean_query.html'):
    p = get_object_or_404(Project, pk=pid)

    if request.user not in p.admin_users():
        raise Http404

    back_or_success = reverse('browse_queries', args=(pid,))

    if request.method == 'POST':
        b = BooleanQuery()
        form = BooleanQueryForm(request.POST, instance=b)
        form.fields['codes'].queryset = p.codes.all()

        if form.is_valid():
            b.project = p
            b.save()

            for code in form.cleaned_data['codes']:
                b.codes.add(code)
            b.save()
            # se actualiza la fecha de modificación 14-06-2014
            p.modified_date = datetime.now()
            p.save()

            return redirect('browse_queries', pid=pid)
    else:
        form = BooleanQueryForm()
        form.fields['codes'].queryset = p.codes.all()

    form_action = reverse('new_boolean_query', args=(pid,))

    return render(request,
                  template,
                  {'form': form,
                   'form_action': form_action,
                   'back_url': back_or_success})


@login_required
def delete_boolean_query(request, pid, qid):
    p = get_object_or_404(Project, pk=pid)
    q = get_object_or_404(BooleanQuery, pk=qid)

    if q.project != p:
        raise Http404

    if request.user not in p.admin_users():
        raise Http404

    for qq in q.containing_queries.all():
        qq.delete()
    q.delete()
    # se actualiza la fecha de modificación 14-06-2014
    p.modified_date = datetime.now()
    p.save()
    return redirect('browse_queries', pid=pid)


@login_required
def new_semantic_query(request, pid, template='new_semantic_query.html'):
    p = get_object_or_404(Project, pk=pid)

    if request.user not in p.admin_users():
        raise Http404

    back_or_success = reverse('browse_queries', args=(pid,))

    if request.method == 'POST':
        q = SemanticQuery()
        form = SemanticQueryForm(request.POST, instance=q)
        form.fields['code'].queryset = p.codes.all()

        if form.is_valid():
            q.project = p
            q.save()
            # se actualiza la fecha de modificación 14-06-2014
            p.modified_date = datetime.now()
            p.save()

            return redirect('browse_queries', pid=pid)
    else:
        form = SemanticQueryForm()
        form.fields['code'].queryset = p.codes.all()

    form_action = reverse('new_semantic_query', args=(pid,))

    return render(request,
                  template,
                  {'form': form,
                   'form_action': form_action,
                   'back_url': back_or_success})


@login_required
def delete_semantic_query(request, pid, qid):
    p = get_object_or_404(Project, pk=pid)
    q = get_object_or_404(SemanticQuery, pk=qid)

    if q.project != p:
        raise Http404

    if request.user not in p.admin_users():
        raise Http404

    q.delete()
    # se actualiza la fecha de modificación 14-06-2014
    p.modified_date = datetime.now()
    p.save()
    return redirect('browse_queries', pid=pid)


@login_required
def new_proximity_query(request, pid, template='new_proximity_query.html'):
    p = get_object_or_404(Project, pk=pid)

    if request.user not in p.admin_users():
        raise Http404

    back_or_success = reverse('browse_queries', args=(pid,))

    if request.method == 'POST':
        q = ProximityQuery()
        form = ProximityQueryForm(request.POST, instance=q)
        form.fields['code1'].queryset = p.codes.all()
        form.fields['code2'].queryset = p.codes.all()

        if form.is_valid():
            q.project = p
            q.save()
            # se actualiza la fecha de modificación 14-06-2014
            p.modified_date = datetime.now()
            p.save()
            return redirect('browse_queries', pid=pid)
    else:
        form = ProximityQueryForm()
        form.fields['code1'].queryset = p.codes.all()
        form.fields['code2'].queryset = p.codes.all()

    form_action = reverse('new_proximity_query', args=(pid,))

    return render(request,
                  template,
                  {'form': form,
                   'form_action': form_action,
                   'back_url': back_or_success})


@login_required
def delete_proximity_query(request, pid, qid):
    p = get_object_or_404(Project, pk=pid)
    q = get_object_or_404(ProximityQuery, pk=qid)

    if q.project != p:
        raise Http404

    if request.user not in p.admin_users():
        raise Http404

    q.delete()
    # se actualiza la fecha de modificación 14-06-2014
    p.modified_date = datetime.now()
    p.save()
    return redirect('browse_queries', pid=pid)


@login_required
def new_set_query(request, pid, template='new_set_query.html'):
    p = get_object_or_404(Project, pk=pid)

    if request.user not in p.admin_users():
        raise Http404

    back_or_success = reverse('browse_queries', args=(pid,))

    if request.method == 'POST':
        s = SetQuery()
        form = SetQueryForm(request.POST, instance=s)
        form.fields['boolean_queries'].queryset = p.boolean_queries.all()
        form.fields['proximity_queries'].queryset = p.proximity_queries.all()
        form.fields['semantic_queries'].queryset = p.semantic_queries.all()

        if form.is_valid():
            s.project = p
            s.save()

            for q in form.cleaned_data['boolean_queries']:
                s.boolean_queries.add(q)
            for q in form.cleaned_data['proximity_queries']:
                s.proximity_queries.add(q)
            for q in form.cleaned_data['semantic_queries']:
                s.semantic_queries.add(q)
            s.save()
            # se actualiza la fecha de modificación 14-06-2014
            p.modified_date = datetime.now()
            p.save()
            return redirect('browse_queries', pid=pid)
    else:
        form = SetQueryForm()
        form.fields['boolean_queries'].queryset = p.boolean_queries.all()
        form.fields['proximity_queries'].queryset = p.proximity_queries.all()
        form.fields['semantic_queries'].queryset = p.semantic_queries.all()

    form_action = reverse('new_set_query', args=(pid,))

    return render(request,
                  template,
                  {'form': form,
                   'form_action': form_action,
                   'back_url': back_or_success})


@login_required
def delete_set_query(request, pid, qid):
    p = get_object_or_404(Project, pk=pid)
    q = get_object_or_404(SetQuery, pk=qid)

    if q.project != p:
        raise Http404

    if request.user not in p.admin_users():
        raise Http404

    q.delete()
    # se actualiza la fecha de modificación 14-06-2014
    p.modified_date = datetime.now()
    p.save()
    return redirect('browse_queries', pid=pid)


def __do_query(request, pid, qid, t, template='browse_query_results.html'):
    p = get_object_or_404(Project, pk=pid)
    query = get_object_or_404(t, pk=qid)

    if query.project != p:
        raise Http404

    citations = query.execute()
    results = {}

    for c in citations:
        for code in c.codes.all():
            if code.id in results:
                results[code.id]['citations'].append(c)
            else:
                results[code.id] = {'id': code.id,
                                    'name': code.name,
                                    'citations': [c]}

    res = results.values()
    return render(request,
                  template,
                  {'project': p,
                   'results': res})


@login_required
def do_boolean_query(request, pid, qid):
    return __do_query(request, pid, qid, BooleanQuery)


@login_required
def do_proximity_query(request, pid, qid):
    return __do_query(request, pid, qid, ProximityQuery)


@login_required
def do_semantic_query(request, pid, qid):
    return __do_query(request, pid, qid, SemanticQuery)


@login_required
def do_set_query(request, pid, qid):
    return __do_query(request, pid, qid, SetQuery)


@login_required
def browse_code_citations(request, cid, pid,template='browse_code_citations.html'):
    c = get_object_or_404(Code, pk=cid)
    citas = Citation.objects.filter(codes=cid)
    return render(request,
              template,
              {'code': c,'citas':citas,'pid':pid})


@login_required
def browse_project_citations(request, pid,template='browse_project_citations.html'):
    form_action = reverse('browse_project_citations',args=(pid,))
    #se cargan los documentos del proyecto
    documentos = DocumentInstance.objects.filter(project_id=pid)
    #se cargan las imágenes del proyecto
    imagenes = ImageInstance.objects.filter(project_id=pid)
    #se pasa a un arreglo los id's de la lista de documentos de dicho proyecto
    documentos_ids = documentos.values_list('id',flat=True)
    # se pasa a un arreglo los id's de la lista de documentos de dicho proyecto
    imagenes_ids = imagenes.values_list('id', flat=True)
    if request.method == 'POST':
        busqueda = request.POST['busqueda']
        #se traen todas las citas de todos los documentos junto con la condición del texto a buscar, el 'i' hace que sea case insensitive
        citas = Citation.objects.filter(document_id__in=documentos_ids, text__icontains=busqueda)
        citas_imagen = ImageCitation.objects.filter(image_id__in=imagenes_ids, comment__icontains=busqueda)
    else:
        #se traen todas las citas de todos los documentos (notese que se envía un arreglo)
        citas = Citation.objects.filter(document_id__in=documentos_ids)
        citas_imagen = ImageCitation.objects.filter(image_id__in=imagenes_ids)
    return render(request,
                  template,
                  {'form_action': form_action,
                   'citas': citas,
                   'citas_imagen': citas_imagen,
                   'pid': pid})


@login_required
def browse_document_citations(request, pid, did,template='browse_document_citations.html'):
    form_action = reverse('browse_document_citations',args=(pid,did,))
    #se cargan los documentos del proyecto
    documentos = DocumentInstance.objects.filter(project_id=pid)
    #se pasa a un arreglo los id's de la lista de documentos de dicho proyecto
    documentos_ids = documentos.values_list('id',flat=True)
    if request.method == 'POST':
        busqueda = request.POST['busqueda']
        #se traén todas las citas de todos los documentos junto con la condición del texto a buscar, el 'i' hace que sea case insensitive
        citas = Citation.objects.filter(document_id__in=documentos_ids,text__icontains=busqueda)
    else:
        #se traén todas las citas de todos los documentos (notese que se envía un arreglo)
        citas = Citation.objects.filter(document_id=did)
    
    response_dict = {
                    'form_action': form_action,
                    'citas':citas,
                    'pid':pid
                    }
    html_response = render_to_string(
                        template, response_dict, RequestContext(request))

    response_data = {'html': html_response}
    return JsonResponse(response_data)

    """return render(request,
                  template,
                  {'form_action': form_action,
                  'citas':citas,
                  'pid':pid})"""


############################################ Inicio Módulo de Imágenes ################################################
@login_required
def view_image(request, pid, did, template='view_image.html'):
    p = get_object_or_404(Project, pk=pid)
    d = get_object_or_404(ImageInstance, pk=did)

    if request.method == 'POST':
        citations = d.citations.all()
        payload={"datos":[]}
        for cit in citations:
            payload["datos"].append({"serial":cit.serialized,"id":cit.id})
        return JsonResponse(payload)
    else:
        texts = {
            'add_code': _(u'Asignar códigos'),
            'add_annotation': _(u'Asignar anotación'),
            'view_details': _('Ver detalles'),
        }
        return render(request,
                      template,
                      {'project': p,
                       'image': d,
                       'citations': d.citations.all(),
                       'texts': texts})


@login_required
def upload_image(request, pid, template='upload_image.html'):
    p = get_object_or_404(Project, pk=pid)

    if request.method == 'POST':
        form = UploadImageForm(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data['name']
            comment = form.cleaned_data['comment']
            image_file = request.FILES['image']
            share = form.cleaned_data['share']
            image = Image(name=name,
                          comment=comment,
                          uploaded_by=request.user,
                          file=image_file,
                          type=splitext(image_file.name)[1],
                          share=share)
            image.save()

            img_instance = ImageInstance(name=name,
                                         project=p,
                                         comment=comment,
                                         image=image,
                                         type=image.type,
                                         uploaded_by=request.user)
            img_instance.save()
            image.file.close()

            # sección para clasificación y guardado de códigos en la base de datos
            path_img = image.file.url
            CLS = Clasificacion_rural(path_img)
            salida = CLS.clasificar()

            if salida == 1:
                print("La imagen es rural!!!", salida)
                DIV = Clasificacion_cobertura(path_img)
                DIV.dividir_imagen()
                DIV.obtener_momentos()
                salida_cobertura_real = DIV.red_neuronal()
                umbral = np.array([0.6655, 0.3936, 0.5175, 0.4249])
                salida_cobertura = np.array_str(1 * (salida_cobertura_real >= umbral))
                coverage = np.transpose(salida_cobertura_real)
                tree = float(np.sum(coverage[0])) / float(len(coverage[0]))
                grass = float(np.sum(coverage[1])) / float(len(coverage[1]))
                ground = float(np.sum(coverage[2])) / float(len(coverage[2]))
                water = float(np.sum(coverage[3])) / float(len(coverage[3]))
                cobertura = Coberturas(id_image=img_instance,
                                       coberturas=salida_cobertura,
                                       parte_x=DIV.parx,
                                       parte_y=DIV.pary,
                                       arbol=tree,
                                       cesped=grass,
                                       suelo=ground,
                                       agua=water)
                cobertura.save()

            else:
                image.share = False
                image.save()
                print("la imagen no es rural", salida)
            return redirect('browse_projects')
    else:
        form = UploadImageForm()
    back_url = reverse('browse_projects')
    form_action = reverse('upload_image', args=(pid,))
    return render(request,
                  template,
                  {'project': p,
                   'form': form,
                   'form_action': form_action,
                   'back_url': back_url})


@login_required
def delete_image(request, pid, did):
    p = get_object_or_404(Project, pk=pid)
    d = get_object_or_404(ImageInstance, pk=did)

    if p.owner == request.user:
        d.image.delete()
        d.delete()
    else:
        raise Http404

    return redirect('browse_projects')


@login_required
def add_code_to_image_citation(request, pid, cid, template='modal.html'):
    if request.method == 'POST':
        form = AddCodeToCitationForm(request.POST)
        p = get_object_or_404(Project, pk=pid)
        cit = get_object_or_404(ImageCitation, pk=cid)

        if form.is_valid():
            response_data = {'success': True}
            for code in form.cleaned_data['codes']:
                if cit.codes.filter(pk=code.pk).exists():
                    response_data = {'error': _('Code already in project')}
                    break
                cit.codes.add(code)
            response_data['cid'] = cid
            response_data['codes_str'] = cit.codes_str()
            response_data['codes_color'] = cit.html_color()
            response_data['top'] = cit.y_coordinate
            response_data['left'] = cit.x_coordinate
            response_data['width'] = cit.width
            return JsonResponse(response_data)
    else:
        p = get_object_or_404(Project, pk=pid)
        cit = get_object_or_404(ImageCitation, pk=cid)
        form = AddCodeToCitationForm()

    form_action = reverse('add_code_to_image_citation',
                          kwargs={'pid': pid, 'cid': cid})
    available_codes = Code.objects.filter(project=p).exclude(pk__in=cit.codes.all())
    form.fields['codes'].queryset = available_codes
    response_dict = {
        'form': form,
        'form_action': form_action,
        'form_header': _(u'Asignar códigos a la imágen'),
    }
    html_response = render_to_string(
        template, response_dict, RequestContext(request))

    response_data = {'html': html_response}
    return JsonResponse(response_data)


@login_required
def image_citation_details(request, pid, cid, template='image_citation_details.html'):
    p = get_object_or_404(Project, pk=pid)
    cit = get_object_or_404(ImageCitation, pk=cid)
    response_dict = {
        'project': p,
        'citation': cit,
        'form_header': _('Detalles de la imagen'),
    }
    html_response = render_to_string(
        template, response_dict, RequestContext(request))

    response_data = {'html': html_response}
    return JsonResponse(response_data)


@login_required
def remove_code_from_image_citation(request, pid, citid, codeid):
    cit = get_object_or_404(ImageCitation, pk=citid)
    code = get_object_or_404(Code, pk=codeid)

    if code not in cit.codes.all():
        raise Http404

    cit.codes.remove(code)
    cit.save()

    return redirect('view_image', pid=pid, did=cit.image.pk)

@login_required
def browse_code_image_citations(request, cid, pid,template='browse_code_image_citations.html'):
    c = get_object_or_404(Code, pk=cid)
    citas = ImageCitation.objects.filter(codes=cid)
    return render(request, template, {'code': c, 'citas': citas, 'pid': pid})

@login_required
def browse_image_citations(request, pid, did, template='browse_image_citations.html'):
    form_action = reverse('browse_image_citations', args=(pid, did,))
    imagenes = ImageInstance.objects.filter(project_id=pid)
    imagenes_ids = imagenes.values_list('id', flat=True)
    if request.method == 'POST':
        busqueda = request.POST['busqueda']
        citas = ImageCitation.objects.filter(image_id__in=imagenes_ids, comment__icontains=busqueda)
    else:
        citas = ImageCitation.objects.filter(image_id=did)
    response_dict = {
        'form_action': form_action,
        'citas': citas,
        'pid': pid
    }
    html_response = render_to_string(template, response_dict, RequestContext(request))
    response_data = {'html': html_response}
    return JsonResponse(response_data)


@login_required
def browse_codes_from_images(request, pid, template='browse_codes_from_images.html'):
    p = get_object_or_404(Project, pk=pid)

    response_dict = {'project': p}
    html_response = render_to_string(
                        template, response_dict, RequestContext(request))

    response_data = {'html': html_response}
    return JsonResponse(response_data)

############################################## Fin Módulo de Imágenes #################################################

