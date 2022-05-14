# -*- coding: utf-8 -*-
from django.utils import simplejson
from django.http import HttpResponse


class JsonResponse(HttpResponse):
    def __init__(self, data, **kwargs):
        content = simplejson.dumps(
                    data,
                    indent=2,
                    ensure_ascii=False)
        super(JsonResponse, self).__init__(
                                    content=content,
                                    mimetype='application/json; charset=utf8',
                                    **kwargs)
