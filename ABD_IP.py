import os
import shlex
import subprocess
import sys


def resolver_adb_path():
    ruta_script = os.path.dirname(__file__)
    return os.path.join(
        ruta_script,
        "platform-tools-latest-windows",
        "platform-tools",
        "adb.exe",
    )


def normalizar_destino_ip(destino):
    destino = destino.strip()
    if not destino:
        return ""

    # Si no se especifica puerto, usamos el default de ADB por TCP
    if ":" not in destino:
        return destino + ":5555"

    host, puerto = destino.rsplit(":", 1)
    if not host:
        return ""
    if not puerto.isdigit():
        return ""
    return destino


def ejecutar_adb(adb_path, args, serial=None):
    comando = [adb_path]
    if serial:
        comando.extend(["-s", serial])
    comando.extend(args)

    try:
        resultado = subprocess.run(comando)
        if resultado.returncode != 0:
            print("ERROR: El comando ADB fallo con codigo", resultado.returncode)
        return resultado.returncode
    except FileNotFoundError:
        print("ERROR: No se encontro adb.exe en la ruta esperada.")
        return 1
    except Exception as e:
        print("ERROR: Fallo al ejecutar ADB:", e)
        return 1


def mostrar_ayuda():
    print("\nComandos utiles:")
    print("- help                 : muestra esta ayuda")
    print("- devices              : lista dispositivos")
    print("- reconnect            : reconecta al ultimo destino IP")
    print("- salir / exit / quit  : cierra el programa")
    print("\nEjemplos:")
    print('- install "C:\\ruta con espacios\\app.apk"')
    print("- shell pm list packages")
    print("- reboot")


def main():
    adb_path = resolver_adb_path()

    if not os.path.exists(adb_path):
        print("ERROR: No se encontro ADB en:")
        print(adb_path)
        print("Revisa la carpeta platform-tools-latest-windows/platform-tools")
        sys.exit(1)

    print("ADB encontrado. Iniciando terminal ADB...")

    try:
        ip_ingresada = input("\nIP de la TV (Enter para saltar y usar USB): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nSalida cancelada por usuario.")
        return

    serial_actual = ""
    ultimo_serial_ip = ""

    if ip_ingresada:
        serial = normalizar_destino_ip(ip_ingresada)
        if not serial:
            print("ERROR: Formato de IP/puerto invalido. Se continua en modo USB.")
        else:
            print("Conectando a", serial, "...")
            rc = ejecutar_adb(adb_path, ["connect", serial])
            if rc == 0:
                serial_actual = serial
                ultimo_serial_ip = serial

    print("\n--- MODO TERMINAL ADB ACTIVO ---")
    print("Escribe help para ayuda, o salir para cerrar.")

    while True:
        objetivo = serial_actual if serial_actual else "USB"
        prompt = "(ADB @ " + objetivo + ") > "

        try:
            entrada = input(prompt).strip()
        except (KeyboardInterrupt, EOFError):
            print("\nCerrando terminal ADB.")
            break

        if not entrada:
            continue

        if entrada.lower() in ["salir", "exit", "quit"]:
            print("Cerrando. Hasta luego.")
            break

        if entrada.lower() == "help":
            mostrar_ayuda()
            continue

        if entrada.lower() == "reconnect":
            if not ultimo_serial_ip:
                print("No hay destino IP previo para reconectar.")
            else:
                print("Reconectando a", ultimo_serial_ip, "...")
                rc = ejecutar_adb(adb_path, ["connect", ultimo_serial_ip])
                if rc == 0:
                    serial_actual = ultimo_serial_ip
            continue

        # Parsea respetando comillas para rutas con espacios
        try:
            partes = shlex.split(entrada, posix=False)
        except ValueError as e:
            print("ERROR en el comando:", e)
            continue

        if not partes:
            continue

        # Si escriben adb por costumbre, lo quitamos
        if partes[0].lower() == "adb":
            partes = partes[1:]
            if not partes:
                continue

        # Si el usuario fuerza -s, no sobreescribimos el destino
        usar_serial = serial_actual
        if "-s" in partes:
            usar_serial = None

        ejecutar_adb(adb_path, partes, serial=usar_serial)


if __name__ == "__main__":
    main()