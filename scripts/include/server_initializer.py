#!/usr/bin/python
# Encoding: UTF-8
# Nombre: server_initializer.py
# Descripcion: Iniciador de servidor HTTP.
# Autor: Agustín González - UNLu
# Modificado: 05/10/15

import sys
import ConfigParser
sys.path.append("include")

from lib import utils
from lib.server import Server


# main(args)
# Punto de entrada de aplicación
def main(args):
    utils.clearscreen()

    try:
        if(len(args) == 2):
            config = ConfigParser.ConfigParser()
            config.read(args[1])

            # Datos de servidor.
            s_host = config.get("SERVER", "Host")
            s_port = config.getint("SERVER", "Port")
            s_webdir = config.get("SERVER", "Webdir")
            s_idxdir = config.get("SERVER", "Idxpath")
            s_errdir = config.get("SERVER", "ErrPath")
            s_logdir = config.get("SERVER", "Logpath")

        elif len(args) == 7:
            s_host = args[1]
            s_port = int(args[2])
            s_webdir = args[3]
            s_idxdir = args[4]
            s_errdir = args[5]
            s_logdir = args[6]
        else:
            print utils.msg_argv
            raw_input()
            sys.exit(0)

        # Inicio de servidor.
        server = Server(s_host, s_port, s_webdir, s_idxdir, s_errdir, s_logdir)
        server.start()
    except KeyboardInterrupt:
        pass
    except Exception, e:
        print utils.msg_file_not_found
        print e
        raw_input()
        sys.exit(0)
    finally:
        # Cierre de servidor.
        server.stop()


# Entrada de aplicación.
if __name__ == "__main__":
    sys.exit(main(sys.argv))
