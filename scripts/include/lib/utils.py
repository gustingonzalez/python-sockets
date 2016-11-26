#!/usr/bin/python
# Encoding: UTF-8
# Nombre: utils.py
# Descripcion: Contiene funciones y clases de utilidad para el TP2.
# Autor: Agustín González - UNLu
# Modificado: 31/10/15

import os
import socket
import urlparse
import hashlib

from urllib import urlencode

# Mensaje de error ARGV genérico.
msg_argv = "No se ha/n especificado el/los parametro/s de configuracion, o no se ha/n delimitado entre comillas."

# Mensaje de error genérico de archivo no encontrado.
msg_file_not_found = "No se ha encontrado el archivo especificado."

# Mensaje de pausa genérico.
msg_pause = "Presione una tecla para continuar..."


# clearscreen()
# Limpia pantalla de forma 'estándar'.
def clearscreen():
    os.system('cls' if os.name == 'nt' else 'clear')


# makedirs(dir)
# Crea el conjunto de directorios especificado sólo en caso que sea necesario.
def makedirs(dir):
    if not os.path.exists(dir):
        print dir
        os.makedirs(dir)


# getpage(url, params, unicode_mode, headers)
# Retorna página (y sus headers, si se especifica) en base a una url y sus
# parámetros, utilizando HTTPClient implementado con sockets.
def getpage(url, params="", unicode_mode=False, headers=False):
    # Importación dentro de función, para no causar referencia circular.
    from httpclient import HTTPClient

    # Encodeo de parametro 'search'.
    url += urlencode(params)

    # Agregación de http:// en caso que sea necesario
    if not urlparse.urlparse(url).scheme:
        url = "http:" + url

    client = HTTPClient()

    # Creación de request.
    http = client.open(url)

    #  Si se requiere en formato unicode
    if unicode_mode:
        # Si se requieren encabezados
        if headers:
            return (unicode(http.read(), "UTF-8"), http.headers)
        else:
            return unicode(http.read(), "UTF-8")
    else:
        if headers:
            return (http.read(), http.headers)
        else:
            return http.read()


# md5(str, is_file)
# Genera hash MD5 en base a mensaje o archivo.
def md5(str, is_file=False):
    # Declaración de objeto hash MD5.
    hash = hashlib.md5()

    if(is_file):
        with open(file) as f:
            # Bloques cada 4096 para no abarcar todo el archivo en memoria.
            for block in iter(lambda: f.read(4096), ""):
                # Update de hash, lo que es igual a
                # hash.update(parte 1 + ... + parte n)
                hash.update(block)
    else:
        hash.update(str)

    # Generación de hash hexadecimal.
    return hash.hexdigest()


# recvstream(socket, buffer_size, delimiter=None)
# Recibe stream de un socket TCP teniendo en cuenta el buffer y el delimitador.
# Si no existe delimitador, la comunicación se cierra cuando el otro extremo
# deja de trasmitir datos.
def recvstream(socket, buffer_size, delimiter=None):
    d = socket.recv(buffer_size)
    data = ""

    while len(d):
        data += d

        if(delimiter):
            if(data.endswith(delimiter)):
                break

        d = socket.recv(buffer_size)

    return data


# addrtostr(address)
# Convierte tupla host:puerto a string.
def addrtostr(address):
    return "{0}:{1}".format(address[0], address[1])


# waitexit()
# Deja consola en modo espera.
def waitexit():
    print "Presione CTRL+C para salir..."

    while True:
        True


# sendto(address, data, wait_response=False, delimiter="")
# Envía los datos especificados a la dirección pasada por parámetro, en base a
# un socket TCP. Si wait_response se encuentra en verdadero, se espera rpta
# desde el otro extremo.
def sendto(address, data, wait_response=False, delimiter=""):

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.connect(address)
    except Exception as e:
        print e
        raise

    s.send(data)

    if(wait_response):
        data = recvstream(s, 2048, delimiter)
        s.close()
        return data

    s.close()

    return None


# Mimetypes
# Clase que contiene tipos mimes y extensiones.
class Mimetypes:
    # Diccionario de mime-types.
    def __init__(self):
        self.__mimetypes = {}

    # getall(self, inverted=False)
    # Retorna los tipos mimes y sus extensiones correspondientes.
    # Inverted, indica si el key debe ser el content-type.
    def getall(self, inverted=False):
        # El archivo se lee una única vez.
        if len(self.__mimetypes) == 0:
            # __file__ hace referencia a directorio actual.
            dir = os.path.relpath(os.path.join(os.path.dirname(__file__),
                                               "mimetypes.txt"))

            for reg in open(dir):
                a = reg.split("	")

                # Entensión como key y content-type como valor de dict.
                self.__mimetypes[a[2]] = a[1]

        if inverted:
            return dict(zip(self.__mimetypes.values(),
                            self.__mimetypes.keys()))

        return self.__mimetypes

    # getmimetype(self, extension)
    # Retorna el mimetype adecuado para una extensión.
    def getmimetype(self, extension):
        mimetypes = self.getall()

        if(extension != ""):
            for mimetype in mimetypes.keys():
                if extension.lower() in mimetype.lower():
                    return mimetypes[mimetype]

        return mimetypes[".txt"]

    # getextension(self, mimetype)
    # Retorna la extensión adecuada para un mimetype pasado por parámetro.
    def getextension(self, mimetype):
        mimetypes = self.getall(inverted=True)
        if(mimetype != ""):
            for mimetype_ in mimetypes.keys():
                if mimetype.lower() in mimetype_.lower():
                    # Split por si hay más de una extensión, ej. jpeg, .jpg
                    return mimetypes[mimetype_].split(",")[0]

        return mimetypes["text/html"]


# CRLFHeader
# Clase idónea para manejar los headers con separación \r\n (CRLF), por ejemplo
# HTTP.
class CRLFHeader:

    # __init__(self, header)
    # Constructor que toma una cabecera CRLF (string o diccionario).
    def __init__(self, header):
        self.header = header

    # todict(self, parse_info=False)
    # Parsea un header CRLF a un diccionario. Si parse_info se encuentra en
    # true, se parsea la información extra como por ejemplo versión HTTP y
    # código de error en caso de un response y versión, path y tipo en caso de
    # un request.
    def todict(self, parse_info=False):
        if type(self.header) is dict:
            return self.header

        header = self.header

        # Parseo de headers mientras el header no comience con HTTP y
        # el len sea mayor a 0.
        headers = {h.split(": ")[0]: h.split(": ")[1] for h in
                   header.split("\r\n") if not h.startswith("HTTP") and
                   len(h) > 0 and len(h.split(": ")) == 2}

        # En caso de una respuesta.
        # Header de petición http (pop para tomar el único elemento de la lista
        # resultante).
        http = [h for h in header.split("\r\n") if h.startswith("HTTP")]

        # Si se requiere parsear información
        if(parse_info):
            if(len(http) > 0):
                # En caso de response.
                http = http.pop().split(" ")

                # Petición y código de error.
                headers["Version"] = http[0]
                headers["Code"] = http[1]
            else:
                # En caso de una petición
                req = [h for h in header.split("\r\n") if h.startswith("GET")]
                if(len(req) > 0):
                    req = req.pop().split(" ")
                    headers["Version"] = req[2]
                    headers["Path"] = req[1]
                    headers["Request-Type"] = req[0]
        else:
            if(len(http) > 0):
                # En caso de response.
                http = http.pop()
                headers[""] = http
            else:
                # En caso de una petición
                req = [h for h in header.split("\r\n") if h.startswith("GET")]
                if(len(req) > 0):
                    req = req.pop()
                    headers[""] = req

        return headers

    # tostring(self)
    # Retorna header en formato string.
    def tostring(self):
        if type(self.header) is str:
            return self.header

        headers = self.header

        # Agregación de header sin key (GET - HTTP).
        str_header = "".join(['%s\r\n' % value for (key, value) in
                             headers.items() if key == ""])

        # Agregación de header restante
        str_header += "".join(['%s: %s\r\n' % (key, value) for (key, value) in
                               headers.items() if key != "" and value != ""])

        str_header += "\r\n"
        return str_header
