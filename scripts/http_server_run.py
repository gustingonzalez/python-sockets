#!/usr/bin/python
# Encoding: UTF-8
# Nombre: http_server_run.py
# Descripción: Servidor HTTP básico que implementa GET y códigos 200 y 400.
# Autor: Agustín González - UNLu
# Modificado: 14/10/15

import sys
import os


def main(args):
    cmd = "python include/server_initializer.py include/config/http_server_run.conf"
    os.system(cmd)

# Entrada de aplicación.
if __name__ == "__main__":
    sys.exit(main(sys.argv))
