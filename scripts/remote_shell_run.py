#!/usr/bin/python
# Encoding: UTF-8
# Nombre: remote_shell_run.py
# Descripción: Terminal remota cliente y servidor.
# Autor: Agustín González - UNLu
# Modificado: 31/10/15

import os
import sys
import time
sys.path.append("include")

from lib import utils
from ConfigParser import ConfigParser


def main(args):

    utils.clearscreen()
    if(len(args) != 2):
        print utils.msg_argv
        sys.exit(0)

    # Lectura de configuración
    config = ConfigParser()
    config.read(args[1])

    s_host = config.get("SERVER", "Host")
    s_port = config.get("SERVER", "Port")
    s_ufile = config.get("SERVER", "UsersFile")
    s_lfile = config.get("SERVER", "LogFile")

    c_host = config.get("CLIENT", "SvrHost")
    c_port = config.get("CLIENT", "SvrPort")

    # Inicialización de servidor.
    cmd = "xterm -e python include/remote_shell_initializer.py "
    args = "server {0} --usersfile {1} --logfile {2} &"

    os.system(cmd + args.format(s_host + ":" + s_port, s_ufile, s_lfile))

    # Inicialización de cliente (500 mls de retraso, para que la conexión
    # con el servidor previamente iniciado sea exitosa).
    time.sleep(0.500)
    cmd = "python include/remote_shell_initializer.py "
    args = "client {0}"
    os.system(cmd + args.format(c_host + ":" + c_port))

# Entrada de aplicación.
if __name__ == "__main__":
    sys.exit(main(sys.argv))
