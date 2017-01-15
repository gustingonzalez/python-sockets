#!/usr/bin/python
# Encoding: UTF-8
# Nombre: basehttpserver.py
# Descripción: Servidor HTTP base que procesa peticiones GET (la
# función do_GET() debe ser implementada en una clase heredada).
# Autor: Agustín González - UNLu
# Modificado: 24/10/15

import os
import socket
import urlparse

from lib import utils
from datetime import datetime
from urllib import unquote_plus


# BaseHTTPServer
# Clase base de servidor HTTP.
class BaseHTTPServer:

    # __init__(self, host, port, webdir, idxpath, errpath, logpath)
    # Constructor que inicia servidor con el host, puerto, directorio web,
    # path de index, path de error 404 y logpath, pasados por parámetro.
    def __init__(self, host, port, webdir, idxpath="", errpath="", logpath=""):
        # Host
        self.host = host

        # Puerto
        self.port = port

        # Directorio de web.
        self.webdir = webdir

        # Path de index.
        self.idxpath = idxpath

        # Path de página de error 404.
        self.errpath = errpath

        # Path de log.
        self.logpath = logpath

        # Inicialización de propiedades privadas
        # Response.
        self.__response = ""

        # Tamaño de buffer de socket.
        self.__buffer = 2048

        # Headers de response.
        self.__headers = ""

        # Estado de servidor
        self.__status = 0

        # Inicialización de Socket
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # start(self)
    # Inicia escucha de servidor.
    def start(self):

        try:
            self.server.bind((self.host, self.port))
            self.server.listen(5)
        except Exception:
            raise

        msg = "Servidor iniciado en {0}:{1}".format(self.host, self.port)
        self.log_message(msg)

        while 1:
            # Vaciamiento de response.
            self.__response = ""

            # Aceptación de conexión TCP.
            client, address = self.server.accept()
            request = client.recv(self.__buffer)

            if(len(request) > 0):
                # Parseo de headers enviados por cliente.
                client_headers = utils.CRLFHeader(request).todict(True)

                # Seteo de path según el header.
                if "http://" not in client_headers["Path"]:
                    # Asignación directa.
                    self.path = client_headers["Path"]
                else:
                    # Parseo de url.
                    parsed_uri = urlparse.urlparse(client_headers["Path"])
                    self.path = parsed_uri.path

                # GET.
                if(client_headers["Request-Type"].split(" ")[0] == "GET"):
                    self.client_headers = client_headers
                    self.do_GET()

                # Impresión de log en pantalla.
                req_type = client_headers["Request-Type"]
                req_path = client_headers["Path"]
                req_vers = client_headers["Version"]
                msg = "\"" + req_type + " " + req_path + " " + req_vers + "\""
                self.log_message(msg)

            # Armado y envío de response.
            content = self.__headers + self.__response
            client.send(content)
            client.close()

    # stop(self)
    # Detiene servidor en curso.
    def stop(self):
        self.server.close()
        self.__status = 0
        self.log_message("Servidor {0}:{1} detenido".format(self.host,
                                                            self.port))

    # do_GET(self)
    # Función GET, que debe ser sobre-escrita en la herencia de la clase.
    def do_GET(self):
        None

    # send_response(self, code)
    # Setea el código de estado HTTP indicado para la respuesta.
    def send_response(self, code):
        # Status: OK.
        if(code == 200):
            # Estado
            self.__headers = "HTTP/1.1 200 OK\r\n"

            # Formato de fecha: Fri, 02 Oct 2015 03:34:24 GMT
            fmt = "%a, %d %b %Y %H:%M:%S GMT"
            fdate = datetime.utcnow().strftime(fmt)
            self.__headers += "Date: {0}\r\n".format(fdate)

            location = self.host + " " + self.path
            self.__headers += "Location: {0}\r\n".format(location)
        # Status: Error.
        elif(code == 404):
            self.__headers = "HTTP/1.0 404 Not Found\r\n"
            self.__headers += "Content-Type: text/html\r\n"
        # Status: Not modified.
        elif(code == 304):
            self.__headers = "HTTP/1.0 304 Not Modified\r\n"

        # Status de response.
        self.__status = code

    # send_error(self, text = "")
    # Envía código y mensaje de error 404 al cliente.
    def send_error(self, text=""):
        self.send_response(404)
        self.end_headers()

        # Si no hay texto a escribir ni página de error por default.
        if(text == "" and self.errpath == ""):
            self.write("404: No encontrado")
        # Si hay texto a escribir.
        elif(text != ""):
            self.write(text)
        # Si está definido errpath
        else:
            try:
                # Establecimiento de path en errpath.
                self.path = self.errpath

                # Retorno de recurso.
                self.write(self.getresource())
            except Exception:
                self.write("404: No encontrado")

    # send_header(self, key, value)
    # Setea el valor del header pasado por parámetro.
    def send_header(self, key, value):
        self.__headers += key + ": " + value + "\r\n"

    # end_headers(self)
    # Finaliza header HTTP con un salto de línea.
    def end_headers(self):
        self.__headers += "\r\n"

    # write(self, text)
    # Realiza escritura en response.
    def write(self, text):
        self.__response = text

    # getresource(self)
    # Retorna HTML en base al path o default path.
    def getresource(self):
        try:
            # Verificación de path.
            if self.path == "/" or self.path == "":
                self.path = self.idxpath

            # Retorno de recurso.
            return open(self.webpath(), "rb").read()
        except Exception:
            raise

    # getresource_mtime(self)
    # Retorna la fecha y hora de modificación del recurso en base al path.
    def getresource_mtime(self):
        try:
            # Verificación de path.
            if self.path == "/" or self.path == "":
                self.path = self.idxpath

            return os.path.getmtime(self.webpath())
        except Exception:
            raise

    # log_message(format, *args)
    # Almacena e imprime log.
    def log_message(self, msg):
        status = self.__status if self.__status != 0 else ""

        date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        log = "{0} | {1} | {2} {3}".format(self.host, date, msg, status)
        print log

        # Append en log.
        if(self.logpath != ""):
            try:
                utils.makedirs(os.path.dirname(self.reallogpath()))
                f = open(self.reallogpath(), "a")
                f.write(log + "\n")
                f.close()
            except Exception:
                raise

    # webpath(self)
    # Retorna el webpath actual, teniendo en cuenta el directorio web.
    def webpath(self):
        p = self.webdir + os.path.sep + unquote_plus(self.path)
        p = os.path.normpath(p)
        return p

    # reallogpath(self)
    # Retorna el logpath real, teniendo en cuenta el directorio del
    # proceso actual.
    def reallogpath(self):
        return os.path.normpath(os.getcwd() + os.sep + self.logpath)
