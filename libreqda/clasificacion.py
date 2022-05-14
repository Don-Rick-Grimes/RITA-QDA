import math
import numpy as np
import scipy.misc
from numpy import genfromtxt
import image_slicer



#Clase para calsificar imagenes rurales vs no rurales
class Clasificacion_rural(object):

    # constructor de la clase
    def __init__(self,nombre_imagen):
        self.nombre_imagen=nombre_imagen
        self.W1 = genfromtxt('pesos/Wyuv1.csv', delimiter=',') #carga la primera capa de pesos de la red neuronal
        self.W2 = genfromtxt('pesos/Wyuv2.csv', delimiter=',') #carga la segunda capa de pesos de la red neuronal
        self.W3 = genfromtxt('pesos/Wyuv3.csv', delimiter=',') #carga la tercera capa de pesos de la red neuronal

    # obtiene los histogramas de una imagen a partir de una matriz RGB
    def clasificar(self):
        self.obtener_histograma_yuv()
        self.red_neuronal()
        return self.Y

    def obtener_histograma_RGB(self):
        imagen_RGB = scipy.misc.imread(self.nombre_imagen)
        rango = np.arange(257,dtype=float) # niveles de cada color 0 - 255
        R , XX = np.histogram(imagen_RGB[:,:,0],rango) # histograma para el color rojo
        R = R.astype(float) # conversion de entero a coma flotante
        R=R/max(R) # normalizacion de datos
        G , XX = np.histogram(imagen_RGB[:,:,1],rango) # histograma para el color verde
        G=G.astype(float) # conversion de entero a coma flotante
        G=G/max(G) # normalizacion de datos
        B , XX = np.histogram(imagen_RGB[:,:,2],rango) # histograma para el color azul
        B=B.astype(float) # conversion de entero a coma flotante
        B=B/max(B) # normalizacion de datos
        histograma = np.concatenate((R,G),axis=0) # concatenamos histogramas de rojo y verde
        self.histograma = np.concatenate((histograma,B),axis=0).T # concatenamos histograma azul con los dos anteriores
        self.histograma=np.insert(self.histograma,len(self.histograma),1) # extension para la red neuronal

    def obtener_histograma_yuv(self):
        imagen_RGB = scipy.misc.imread(self.nombre_imagen)
        rango = np.arange(257,dtype=float) # niveles de cada color 0 - 255
        imagen_RGB = imagen_RGB/255.0
        Y = 0.299*imagen_RGB[:,:,0]+0.587*imagen_RGB[:,:,1]+0.114*imagen_RGB[:,:,2] # obtencion de la luminancia
        U = 0.493*(imagen_RGB[:,:,2]-Y) # obtencion de la crominancia U
        V = 0.877*(imagen_RGB[:,:,0]-Y) # obtencion de la crominancia V


        Y = (255*Y).astype(np.uint8) # mapeo de los valores al intervalo 0 - 255
        Yh , XX = np.histogram(Y,rango) # obtencion del histograma de la luminancia
        Yh = Yh/float(max(Yh)) # normalizacion de datos

        U = ((255*U/0.872)+127.5).astype(np.uint8) # mapeo de los valores al intervalo 0 - 255
        Uh , XX = np.histogram(U,rango) # obtencion del histograma de la crominancia U
        Uh = Uh/float(max(Uh)) # normalizacion de datos

        V = ((255*V/1.23) + 127.5).astype(np.uint8) # mapeo de los valores al intervalo 0 - 255
        Vh , XX = np.histogram(V,rango) # obtencion del histograma de la crominancia V
        Vh = Vh/float(max(Vh)) # normalizacion de datos


        histograma = np.concatenate((Yh,Uh),axis=0)
        histograma = np.concatenate((histograma,Vh),axis=0)
        self.histograma = np.insert(histograma,len(histograma),1)

    # clasifica Una imagen a partir de un histograma RGB
    def red_neuronal(self):
        G= np.dot(self.histograma,self.W1)#paso por la capa 1
        # print(G)
        G1=1/(1+np.exp(-G))#funcion de activacion de la capa1
        G1=np.insert(G1,len(G1),1)
        G = np.dot(G1,self.W2)#paso por la capa 2
        # print(G)
        G2=1/(1+np.exp(-G))#funcion de activacion de la capa2
        G2=np.insert(G2,len(G2),1)
        G = np.dot(G2,self.W3)#paso por la capa 3
        # print(G)
        self.Y=1/(1+np.exp(-G))#funcion de activacion de la capa3
        # print(self.Y)
        if self.Y>= 0.0036:
            self.Y=1
        else:
            self.Y=0
        # print int(self.Y)#salida de la red neuronal



class Clasificacion_cobertura(object):

    def __init__(self, nombre_imagen):
        self.nombre_imagen = nombre_imagen
        self.momentos = np.array([0,0,0,0,0,0,0,0,0,0])
        self.imagen_RGB = scipy.misc.imread(self.nombre_imagen)
        self.imagen_RGB = self.imagen_RGB.astype(float)
        self.ancho,self.alto,XX=self.imagen_RGB.shape
        self.W1 = genfromtxt('pesos/Wmc1.csv', delimiter=',') # carga la primera capa de pesos de la red neuronal
        self.W2 = genfromtxt('pesos/Wmc2.csv', delimiter=',') # carga la segunda capa de pesos de la red neuronal
        #self.W3 = genfromtxt('libreqda/pesos/W3.csv', delimiter=',') #carga la tercera capa de pesos de la red neuronal

    def clasificar(self):

        self.obtener_momentos()
        self.red_neuronal()
        return self.Y

    def obtener_momentos(self):

        for tile in self.tiles:
            img = np.array(tile.image)
            ancho, alto, XX = img.shape
            P= float(ancho*alto)
            # Media: primer momento de color
            Er = (np.sum(img[:,:,0]))/P # media de la banda roja de la imagen
            Eg = (np.sum(img[:,:,1]))/P # media de la banda verde de la imagen
            Eb = (np.sum(img[:,:,2]))/P # media de la banda azul de la imagen
            E = {'red':Er,'green':Eg,'blue':Eb}
            # Desviacion standar: segundo momento de color
            Dr = (np.sum((np.around(img[:,:,0]-Er).astype(np.uint8)**2.0).astype(np.uint8))/P)**(1.0/2.0) # Desviacion standar para la banda roja
            Dg = (np.sum((np.around(img[:,:,1]-Eg).astype(np.uint8)**2.0).astype(np.uint8))/P)**(1.0/2.0) # Desviacion standar para la banda verde
            Db = (np.sum((np.around(img[:,:,2]-Eb).astype(np.uint8)**2.0).astype(np.uint8))/P)**(1.0/2.0) # Desviacion standar para la banda azul
            D = {'red':Dr,'green':Dg,'blue':Db}
            # Simetria : tercer momento de color
            Skr = (np.sum((np.around(img[:,:,0]-Er).astype(np.uint8)**3.0).astype(np.uint8))/P)**(1.0/3.0) # Simetria para la banda roja
            Skg = (np.sum((np.around(img[:,:,1]-Eg).astype(np.uint8)**3.0).astype(np.uint8))/P)**(1.0/3.0) # Simetria para la banda verde
            Skb = (np.sum((np.around(img[:,:,2]-Eb).astype(np.uint8)**3.0).astype(np.uint8))/P)**(1.0/3.0) # Simetria para la banda azul
            Sk = {'red':Skr,'green':Skg,'blue':Skb}
            momento = (np.array([E["red"],D["red"],Sk["red"],E["green"],D["green"],Sk["green"],E["blue"],D["blue"],Sk["blue"],1])).T
            self.momentos = np.vstack([self.momentos,momento])
        self.momentos = np.delete(self.momentos,0,0)


    def obtener_histograma(self):
        # imagen_RGB = scipy.misc.imread(self.nombre_imagen)
        rango = np.arange(257,dtype=float) # niveles de cada color 0 - 255
        R , XX = np.histogram(self.imagen_RGB[:,:,0],rango) # histograma para el color rojo
        R = R.astype(float) # conversion de entero a coma flotante
        R=R/max(R) # normalizacion de datos
        G , XX = np.histogram(self.imagen_RGB[:,:,1],rango) # histograma para el color verde
        G=G.astype(float) # conversion de entero a coma flotante
        G=G/max(G) # normalizacion de datos
        B , XX = np.histogram(self.imagen_RGB[:,:,2],rango) # histograma para el color azul
        B=B.astype(float) # conversion de entero a coma flotante
        B=B/max(B) # normalizacion de datos
        histograma = np.concatenate((R,G),axis=0) # concatenamos histogramas de rojo y verde
        histograma = np.concatenate((histograma,B),axis=0).T # concatenamos histograma azul con los dos anteriores
        self.histograma=np.insert(histograma,len(histograma),1) # extension para la red neuronal



    def dividir_imagen(self):
        parx = math.ceil(self.ancho/128.0)
        pary = math.ceil(self.alto/128.0)
        partes = parx*pary# numero de partes en los que se dividira la imagen
        #print(parx)
        #print(pary)
        #print(partes)
        self.tiles = image_slicer.slice(self.nombre_imagen, partes, save=False)
        self.parx = parx
        self.pary = pary

    def red_neuronal(self):
        G= np.dot(self.momentos,self.W1)#paso por la capa 1
        G1=1/(1+np.exp(-G))#funcion de activacion de la capa1
        xx, yy = G1.shape
        G1 = (np.vstack([G1.T, np.ones(xx)])).T
        G = np.dot(G1,self.W2)#paso por la capa 2
        Y=1/(1+np.exp(-G))#funcion de activacion de la capa3
        #umbrales de calsificacion
        #arboles 0.6655
        #cesped 0.3936
        #suelo descubierto 0.5175
        #cuerpos de agua 0.4249
        self.Y = Y
        return self.Y



