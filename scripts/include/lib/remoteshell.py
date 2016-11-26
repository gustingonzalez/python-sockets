#!/usr/bin/python
# Encoding: UTF-8
# Nombre: remoteshell.py
# Descripción: Terminal remota cliente y servidor. Son requeridas las librerías
# "pycrypto" y "rsa" (pip install pycrypto / pip install rsa)
# Autor: Agustín González - UNLu
# Modificado: 24/10/15

import sys
import os
import rsa
import utils
import socket
import base64
import getpass
import subprocess


from datetime import datetime
from Crypto.Cipher import AES


# ShellServer
# Servidor de terminal remota.
class ShellServer:

    # __init__(self, address, users_file, log_file="", create_user=False)
    # Constructor.
    def __init__(self, address, users_file, log_file="", create_user=False):
        utils.clearscreen()
        self.address = address

        # abspath, ya que con el comando 'cd' del cliente, el directorio
        # relativo puede cambiar.
        self.users_file = os.path.abspath(users_file)

        if log_file != "" and log_file is not None:
            self.log_file = os.path.abspath(log_file)
        else:
            self.log_file = ""

        self.__buffer_size = 2048
        self.__backlog = 5
        self.__create_user = create_user

    # start(self)
    # Inicia el servidor de shell remota.
    def start(self):
        msg = "Servidor shell remoto iniciado en {0}:{1}"
        print msg.format(self.address[0], self.address[1])

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.address[0], self.address[1]))
        server.listen(self.__backlog)

        # Modo de creación de usuario.
        if(self.__create_user):
            self.log("Modo de creación de usuario...")
            self.create_user()

        # Creación de archivo si no existe o si no hay usuarios.
        if(not self.has_users()):
            self.log("No hay usuarios...")
            self.create_user()

        client, address = server.accept()
        self.log("Cliente conectado: {0}:{1}".format(address[0], address[1]))

        # Intercambio de claves y obtención de clave AES.
        cryptor = self.exchange_keys(server, client)

        # Autenticación de usuario.
        if (not self.autenticate_user(cryptor, server, client)):
            # En caso de autenticación fallida, salida de app.
            sys.exit(-1)

        os.chdir("/home")
        print "\n"

        while 1:
            cmd = client.recv(self.__buffer_size)
            cmd = decrypt(cryptor, cmd)
            print ">>>", cmd
            self.log("Recibido: " + cmd)
            try:
                # Cambio de directorio en caso de comando cd.
                if(cmd.startswith("cd")):
                    cmd = cmd.split(" ")
                    if(len(cmd) == 2):
                        os.chdir(cmd[1])
                        out, err = "", ""
                    else:
                        out = ""
                        err = "Argumentos incorrectos o insuficientes.\n"
                # Imposibilidad de ejecución de comando sudo.
                elif(cmd.startswith("sudo")):
                    err = "Imposible ejecutar sudo."
                # Ejecución en consola.
                else:
                    out, err = self.execute(cmd)
            except Exception as e:
                err = str(e) + "\n"
                pass

            msg = "\n"
            if(out != "" and err != ""):
                msg = out + "\n" + err
            elif(out != ""):
                msg = out
            elif(err != ""):
                msg = err

            self.log("Enviado: " + msg, show=False)
            crypto = encrypt(cryptor, msg)
            client.send(crypto)

    # autenticate_user(self, cryptor, server, client)
    # Realiza autenticación de usuario (3 intentos de error máximo). Retorna
    # true en caso de que esta sea correcta.
    def autenticate_user(self, cryptor, server, client):
        # Recepción de mensaje encriptado.
        crypto = client.recv(self.__buffer_size)

        # Desencriptación.
        msg = decrypt(cryptor, crypto)

        # Sppliteo usuario, contraseña.
        spplited = msg.split("|")

        # Contador de intentos.
        intents = 1

        # Mientras no se superen los 3 intentos fallidos.
        while intents < 3:
            if(self.exists_user(spplited[0], spplited[1])):
                client.send(encrypt(cryptor, msg))
                self.log("Autenticación realizada...")
                return True
            else:
                # Envío de autenticación fallida al cliente.
                self.log("Autenticación fallida...")
                client.send(encrypt(cryptor, "unauthorized"))

                # Recepción de datos de reintento.
                crypto = client.recv(self.__buffer_size)
                msg = decrypt(cryptor, crypto)
                spplited = msg.split("|")
            intents += 1

        client.close()
        server.close()

        # Autenticación fallida.
        return False

    # create_user(self)
    # Modo de creación de usuario.
    def create_user(self):
        try:
            usr = raw_input(">>> Nombre de usuario: ")
            pwd = getpass.getpass(">>> Password: ")

            self.add_user(usr, pwd)
        except Exception as e:
            print str(e) + "\n"
            self.create_user()

    # has_users(self)
    # Verifica si existen usuarios en el archivo seteado.
    def has_users(self):

        # Creación de archivo en caso que no exista.
        if(not os.path.isfile(self.users_file)):
            if(os.path.dirname(self.users_file) != ""):
                utils.makedirs(os.path.dirname(self.users_file))
                open(self.users_file, "w")

        # Verificación de existencia.
        try:
            f = open(self.users_file, "r")
            for line in f:
                spplited = line.rstrip().split("=")
                if(spplited[0].lower().strip() == "usr"):
                    return True
            return False
        except Exception:
            return False

    # exists_user(self, usr, pwd="")
    # Verifica si existe un usuario pasado por parámetro. Si pwd es distinto
    # de vacío, se verifican tanto usuario como contraseña.
    def exists_user(self, usr, pwd=""):
        if(self.has_users()):
            f = open(self.users_file, "r")

            for line in f:
                spplited = line.split("=")

                # Si la primera parte es nombre
                if(spplited[0].lower().strip() == "usr"):
                    if(spplited[1].strip() == usr):
                        # Si no es necesario verificar contraseña
                        if(pwd.strip() == ""):
                            return True
                        # Verificación de contraseña.
                        else:
                            line = f.next()
                            spplited = line.split("=")

                            if(spplited[0].lower().strip() == "pwd"):
                                if(spplited[1].strip() == pwd):
                                    return True
        else:
            return False

    # add_user(self, usr, pwd)
    # Agrega un usuario + contraseña pasados por parámetro al archivo de
    # usuarios.
    def add_user(self, usr, pwd):

        # Hash MD5 de usuario y pwd.
        usr_md5 = utils.md5(usr)
        pwd_md5 = utils.md5(pwd)

        if(usr.strip() == ""):
            raise Exception("El nombre de usuario no puede ser vacío.")
        elif(pwd.strip() == ""):
            raise Exception("La contraseña de usuario no puede ser vacía.")

        # Verificación de no existencia del usuario a agregar.
        if not self.exists_user(usr_md5):
            f = open(self.users_file, "a")
            f.write("usr=" + usr_md5 + "\n")
            f.write("pwd=" + pwd_md5 + "\n")
            f.write("\n")
            self.log("Creación de usuario finalizada...")
        else:
            raise Exception("El usuario {0} ya existe.".format(usr))

    # exchange_keys(self, server, client)
    # Realiza el intercambio de claves con el cliente.
    def exchange_keys(self, server, client):
        # Generación de clave pública y privada.
        pub_key, priv_key = rsa.newkeys(512)

        # Envío de clave pública a cliente.
        public_key_msg = "key|" + str(pub_key.n) + "|" + str(pub_key.e)
        client.send(public_key_msg)

        # Recepción de clave AES encriptada.
        data = client.recv(1024)
        aes_key_msg = rsa.decrypt(data.split("|")[1], priv_key)

        # Retorno de encriptador, desencriptador.
        return AES.new(aes_key_msg, AES.MODE_CFB, aes_key_msg)

    # execute(self, cmd)
    # Ejecuta el comando indicado como parámetro.
    def execute(self, cmd):
        p = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdin=subprocess.PIPE,
                             shell=True)

        out, err = p.communicate()
        return out, err

    # log(self, msg, show=True)
    # Almacena mensaje de log pasado por parámetro. Si show es True, se muestra
    # el mensaje en la consola/terminal.
    def log(self, msg, show=True):
        address = self.address[0] + ":" + str(self.address[1])
        date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        log = "{0} | {1} | {2}".format(address, date, msg)

        if show:
            print msg

        # Append en log.
        if(self.log_file != ""):
            try:
                utils.makedirs(os.path.dirname(self.log_file))
                f = open(self.log_file, "a")
                f.write(log + "\n")
                f.close()
            except Exception, e:
                print e
                raise


# ShellClient
# Cliente de terminal remota.
class ShellClient:

    # __init__(self, svr_address)
    # Constructor.
    def __init__(self, svr_address):
        self.svr_address = svr_address
        self.__buffer_size = 2048

    # start(self)
    # Inicia servidor de shell remota, conectandóse al servidor especificado
    # en el constructor.
    def start(self):
        utils.clearscreen()
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.connect((self.svr_address[0], self.svr_address[1]))

        # Intercambio de claves y obtención de clave AES. Cryptor representa
        # el nuevo encriptador, desencriptador.
        cryptor = self.exchange_keys(server)

        # Autenticación de usuario
        if not self.autenticate_user(cryptor, server):
            server.close()
            print "\n"
            sys.exit(-1)

        print "\n"

        while(True):
            # Envío de consulta de directorio.
            server.send(encrypt(cryptor, "pwd"))

            # Recepción de directorio.
            crypto, address = server.recvfrom(self.__buffer_size)

            # Desencriptación de mensaje recibido.
            curdir = decrypt(cryptor, crypto)

            # Ingreso de comando de usuario.
            cmd = str(raw_input(">>> " + curdir.replace("\n", "") + "$ "))
            server.send(encrypt(cryptor, cmd))
            crypto, address = server.recvfrom(self.__buffer_size)

            # Impresión de respuesta de comando.
            print decrypt(cryptor, crypto)

    # exchange_keys(self, server)
    # Realiza el intercambio de claves con el servidor.
    def exchange_keys(self, server):

        # Repceción de clave pública del servidor.
        aux = server.recv(self.__buffer_size).split("|")
        server_pub_key = rsa.PublicKey(long(aux[1]), long(aux[2]))

        # Generación de clave AES: 128 bits, 16 bytes.
        aes_key_msg = os.urandom(16)

        # Envío de clave AES, encriptada con clave pública recibida.
        server.send("key|" + rsa.encrypt(aes_key_msg, server_pub_key))

        # Retorno de encriptador, desencriptador.
        return AES.new(aes_key_msg, AES.MODE_CFB, aes_key_msg)

    # autenticate_user(self, cryptor, server)
    # Realiza autenticación de usuario contra el servidor.
    def autenticate_user(self, cryptor, server):
        status = "unauthorized"

        # Mientras estado sea desautorizado.
        while status == "unauthorized":
            print "Autenticación:"

            usr = raw_input(">>> Usuario: ")
            pwd = getpass.getpass(">>> Password: ")

            # Hash MD5 de user y pwd.
            usr_md5 = utils.md5(usr)
            pwd_md5 = utils.md5(pwd)

            # Envío de datos de usuario a servidor.
            server.send(encrypt(cryptor, usr_md5 + "|" + pwd_md5))

            crypto = server.recv(self.__buffer_size)
            status = decrypt(cryptor, crypto)
            if(status == "unauthorized"):
                print "Usuario o contraseña incorrectos.\n"

        # Si el servidor no envía datos, significa que la autenticación ha
        # sido fallida.
        if(crypto == ""):
            print "Se ha superado el número máximo de intentos..."
            return False

        return True


# encrypt(cryptor, msg)
# Realiza encriptación y encodea a base64 teniendo en cuenta el des/encriptador
# y mensaje pasados por parámetro.
def encrypt(cryptor, msg):
    return base64.b64encode(cryptor.encrypt(msg))


# decrypt(cryptor, msg)
# Desencodea de base 64 y realiza desencriptación teniendo en cuenta el
# des/encriptador y mensaje pasados por parámetro.
def decrypt(cryptor, msg):
    return cryptor.decrypt(base64.b64decode(msg))
