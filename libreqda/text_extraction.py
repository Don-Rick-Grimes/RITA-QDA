# -*- coding: utf-8 -*-
import cStringIO
from pdfminer.pdfinterp import PDFResourceManager, process_pdf
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams

from docx import opendocx, getdocumenttext
from pyth.plugins.rtf15.reader import Rtf15Reader

import os
from os.path import splitext

def txt(f):
    with open(f, 'r') as f:
        return '\r\n'.join(f.readlines())


def pdf(f):

    #¡IMPORTANTE! funcionalidad antígua de extracción de texto de pdf

    """rsrcmgr = PDFResourceManager()
    retstr = cStringIO.StringIO()
    codec = 'utf-8'

    laparams = LAParams()
    laparams.all_texts = True

    device = TextConverter(
        rsrcmgr, retstr, codec=codec, laparams=laparams
    )

    fp = file(f, 'rb')
    process_pdf(rsrcmgr, device, fp)
    fp.close()
    device.close()

    str = retstr.getvalue()
    retstr.close()
    return str
    """
    
    #¡IMPORTANTE! nueva funcionalidad de pdf a html 
    #pdftohtml = 'pdftohtml -i -s -noframes '+f #sin imágenes
    pdftohtml = 'pdftohtml -s -noframes '+f
    os.system(pdftohtml)
    rutaArchivo = os.path.dirname(f)+'/'+splitext(os.path.basename(f))[0]+'.html'
    myfile = open(rutaArchivo, 'r')
    data = myfile.read()
    return data


def docx(f):
    doc = opendocx(f)
    return '\r\n'.join(getdocumenttext(doc))


def rtf(f):
    with open(f, "rb") as f:
        doc = Rtf15Reader.read(f)
    result = []
    for element in doc.content:
        for text in element.content:
            result.append(''.join(text.content))
    return '\r\n'.join(result)

