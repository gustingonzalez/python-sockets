#!/usr/bin/python
# Encoding: UTF-8
# Nombre: server.py
# Descripción: Servidor HTTP que hereda funcionalidades del módulo
# BaseHTTPServer (propio, no de Python).
# Autor: Agustín González - UNLu
# Modificado: 31/10/15

import os
import traceback

from lib import utils
from datetime import datetime, timedelta
from lib.basehttpserver import BaseHTTPServer


# Server
# Clase que reescribe método do_GET() de BaseHTTPServer
class Server(BaseHTTPServer):

    # do_GET(self)
    # Método que es llamado cuando se realiza una petición GET al servidor.
    def do_GET(self):

        # Contenido HTTP.
        content = ""

        try:
            # Verificación de respuesta 304 (No MODIFICADO)
            if "If-Modified-Since" in self.client_headers.keys():
                # Fecha de cabecera.
                # Formato: Mon, 06 Aug 2012 11:59:26 GMT
                fmt = "%a, %d %b %Y %H:%M:%S GMT"
                modified_since = self.client_headers["If-Modified-Since"]
                modified_since = datetime.strptime(modified_since, fmt)
                print modified_since

                # Fecha de modificación de recurso.
                modified = self.getresource_mtime()
                modified = datetime.fromtimestamp(modified)
                modified = modified - timedelta(hours=-3)

                # Si el recurso no ha sido modificado desde la fecha de modif.
                # envíada en la cabecera
                if(modified_since >= modified):
                    # Retorno de respuesta 304.
                    self.send_response(304)
                    self.send_header('Content-Length', "0")
                    self.end_headers()
                    return

            # Si la extensión se encuentra en mimetypes (por defecto .txt).
            extension = os.path.splitext(self.path)[1]
            # Verificación de extensión y mimetype.
            if(extension != ""):
                mimetype = utils.Mimetypes().getmimetype(extension)
            else:
                mimetype = utils.Mimetypes().getall()[".html"]

            # Obtención de contenido en base a path.
            content = self.getresource()

            # Seteo de html y headers básicos.
            self.send_response(200)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Cache-Control', "max-age=604800")
            self.send_header('Content-Type', mimetype)
            self.end_headers()
            self.write(content)
        except Exception:
            # print traceback.print_exc()
            # print e
            self.send_error()
            return
