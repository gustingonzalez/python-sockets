#!/usr/bin/python
# Encoding: UTF-8
# Nombre: remote_shell_initializer.py
# Descripción: Iniciador de shell remota cliente o servidor.
# Autor: Agustín González - UNLu
# Modificado: 31/10/15

import sys
import argparse

from lib.remoteshell import ShellServer, ShellClient


def main(args):
    parser = initparser()

    args = parser.parse_args()

    try:
        # Modo servidor.
        address = (args.address.split(":")[0], int(args.address.split(":")[1]))
        if(args.mode == "server"):
            server = ShellServer(address, args.usersfile,
                                 args.logfile, args.createuser)
            server.start()
        # Modo cliente
        else:
            client = ShellClient(address)
            client.start()
    except Exception as e:
        print e
        raw_input("Ha ocurrido un error...")


# initparser()
# Inicializa y retorna parser.
def initparser():
    p = argparse.ArgumentParser(description="Shell remota")

    p.add_argument('mode', choices=("server", "client"),
                   help="Permite especificar el modo de ejecución del " +
                   "protocolo (server o client)")

    # Verificación de argumento posicional mode
    mode = p.parse_args(sys.argv[1:2]).mode

    help = "Host y puerto de servidor"
    p.add_argument("address", help=help, metavar="HOST:PORT")


    # Si modo seleccionado es servidor, se añaden parámetros necesarios.

    if(mode == "server"):
        help = "Archivo que contiene usuarios válidos para la autenticación"
        help += "del cliente. Si este no existe, será creado y se solicitará"
        help += "un primer usuario"
        p.add_argument("--usersfile", required=True, help=help)

        "Archivo log de servidor"
        p.add_argument("--logfile", help=help)

        help = "Inicia el servidor en modo de creación de usuario"
        p.add_argument("--createuser", action="store_true", default=False,
                       help=help)

    return p

if __name__ == "__main__":
    sys.exit(main(sys.argv))
