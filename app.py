"""
app.py - Servidor Flask: conecta Python (la lógica) con la interfaz web.

Rutas:
    GET  /               -> muestra la interfaz (templates/index.html)
    POST /api/construir  -> valida la entrada, construye el ABB y devuelve los pasos de inserción
    GET  /api/inorden    -> devuelve el resultado y los pasos del recorrido Inorden
    POST /api/reiniciar  -> olvida el árbol actual

La comunicación se hace con JSON. JavaScript no calcula nada del árbol:
solo pide los datos a estas rutas y los dibuja.
"""

import inspect
import json
import re
import textwrap
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from arbol import ArbolABB, Nodo

app = Flask(__name__)

CARPETA = Path(__file__).resolve().parent

# JavaScript solo representa sin error los enteros hasta 2^53 - 1.
LIMITE_JS = 9007199254740991

# Estado del programa: el último árbol construido.
estado = {"arbol": None}


# Validacuión de la entrada del usuario: convierte el texto en una lista de enteros.
def listar(elementos, maximo=8):
    """Une los elementos con comas; si son muchos, resume los que sobran."""
    texto = ", ".join(elementos[:maximo])
    if len(elementos) > maximo:
        texto += f" (y {len(elementos) - maximo} más)"
    return texto


def validar_entrada(texto):
    """
    Convierte el texto escrito por el usuario en una lista de números enteros.
    Devuelve (valores, errores, avisos).
      * Si `errores` trae mensajes, el árbol NO se construye.
      * Los valores repetidos no son un error: se toma uno solo (el primero) y se informa en `avisos`.
    """
    errores, avisos = [], []

    # Separar por comas, punto y coma, espacios o saltos de línea.
    partes = [p for p in re.split(r"[,;\s]+", texto) if p != ""]
    if len(partes) == 0:
        return [], ["La entrada está vacía. Escribe al menos 2 números enteros."], []

    #Revisar cada dato y clasificarlo.
    valores, no_numericos, decimales, fuera_de_rango = [], [], [], []
    for parte in partes:
        if re.fullmatch(r"[+-]?[0-9]+", parte):                       # entero válido
            signo = -1 if parte.startswith("-") else 1
            digitos = parte.lstrip("+-").lstrip("0")                  # sin signo ni ceros a la izquierda
            if len(digitos) > 16:                                     # demasiadas cifras
                fuera_de_rango.append(parte)
            else:
                numero = signo * int(digitos or "0")
                if abs(numero) > LIMITE_JS:
                    fuera_de_rango.append(parte)
                else:
                    valores.append(numero)
        elif re.fullmatch(r"[+-]?([0-9]+\.[0-9]*|\.[0-9]+)", parte):  # decimal
            decimales.append(parte)
        else:                                                         # letras, símbolos, etc.
            no_numericos.append(parte)

    # 3) Preparar un mensaje claro por cada problema encontrado.
    if no_numericos:
        errores.append("Hay datos que no son números: " + listar(no_numericos) + ".")
    if decimales:
        errores.append("Solo se aceptan enteros; estos son decimales: " + listar(decimales) + ".")
    if fuera_de_rango:
        errores.append(f"Fuera del rango seguro de JavaScript (±{LIMITE_JS}): " + listar(fuera_de_rango) + ".")
    if len(partes) < 2:
        errores.append("Se necesitan al menos 2 números (escribiste 1).")

    #Valores repetidos: se toma uno solo (el primero que aparece) y se avisa cuáles eran.
    veces = {}
    for numero in valores:
        veces[numero] = veces.get(numero, 0) + 1
    repetidos = [f"{numero} ({n} veces)" for numero, n in veces.items() if n > 1]
    if repetidos:
        avisos.append("Valores repetidos: se usó una sola vez " + listar(repetidos) + ".")
        valores = list(veces)                 # el diccionario conserva el orden de primera aparición
        if len(valores) < 2 and not (no_numericos or decimales or fuera_de_rango):
            errores.append("Todos los números son iguales: se necesitan al menos 2 números distintos.")

    return valores, errores, avisos


#Rutas
@app.route("/")
def ruta_inicio():
    return render_template("index.html", codigo=codigo_de_ayuda(), ejemplo=ejemplos_de_ayuda())


@app.route("/api/construir", methods=["POST"])
def ruta_construir():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        datos = {}
    valores, errores, avisos = validar_entrada(str(datos.get("texto", "")))
    if errores:
        return jsonify({"ok": False, "errores": errores}), 400    # entrada inválida: no se construye nada

    arbol = ArbolABB()
    try:
        pasos = arbol.construir(valores)         # inserta los números en el orden recibido
        resumen = arbol.a_diccionario()          # raíz, cantidad, altura y nodos para dibujar
    except RecursionError:
        mensaje = "El árbol quedó demasiado profundo (más de unos 900 niveles). Prueba con menos números ordenados."
        return jsonify({"ok": False, "errores": [mensaje]}), 400

    estado["arbol"] = arbol
    return jsonify({"ok": True, "valores": valores, "arbol": resumen, "pasos_insercion": pasos, "avisos": avisos})


@app.route("/api/inorden")
def ruta_inorden():
    arbol = estado["arbol"]
    if arbol is None:
        return jsonify({"ok": False, "errores": ["Primero construye el árbol."]}), 409

    resultado = arbol.inorden()                  # resultado ascendente: sale del recorrido, sin ordenar
    pasos = arbol.generar_pasos_inorden()        # eventos para animar el recorrido

    # Comprobación: la animación debe visitar exactamente lo mismo que devuelve inorden().
    visitados = [paso["valor"] for paso in pasos if paso["tipo"] == "visitar"]
    if visitados != resultado:
        return jsonify({"ok": False, "errores": ["Error interno: los pasos no coinciden con inorden()."]}), 500

    return jsonify({"ok": True, "resultado": resultado, "pasos": pasos})


@app.route("/api/reiniciar", methods=["POST"])
def ruta_reiniciar():
    estado["arbol"] = None
    return jsonify({"ok": True})


# DATOS REALES PARA LA SECCIÓN AYUDA Y ALGORITMOs
# (el código y los ejemplos se leen y ejecutan desde los propios archivos,
#  así la ayuda siempre coincide con lo que de verdad hace el programa)
def codigo_python(*objetos):
    """Código fuente REAL de clases, métodos o funciones (se lee con inspect)."""
    return "\n\n".join(textwrap.dedent(inspect.getsource(o)).rstrip() for o in objetos)


def codigo_js(nombre):
    """Texto REAL de un bloque de static/js/app.js marcado con  // [AYUDA: nombre]  ...  // [/AYUDA]."""
    texto = (CARPETA / "static" / "js" / "app.js").read_text(encoding="utf-8")
    bloque = re.search(r"// \[AYUDA: " + re.escape(nombre) + r"\]\n(.*?)// \[/AYUDA\]", texto, re.S)
    return bloque.group(1).rstrip() if bloque else "(bloque no encontrado en app.js)"


def codigo_de_ayuda():
    return {
        "nodo": codigo_python(Nodo),
        "arbol": "class ArbolABB:\n" + inspect.getsource(ArbolABB.__init__).rstrip(),
        "insertar": codigo_python(ArbolABB.insertar),
        "inorden": codigo_python(ArbolABB.inorden, ArbolABB._inorden),
        "pasos": codigo_python(ArbolABB.generar_pasos_inorden, ArbolABB._pasos_inorden),
        "dibujo": codigo_js("dibujo"),
        "ruta_construir": codigo_python(ruta_construir),
        "js_comunicacion": codigo_js("comunicacion"),
        "validacion": codigo_python(validar_entrada),
        "reproductor": codigo_js("reproductor"),
        "ruta_inorden": codigo_python(ruta_inorden),
        "js_resultado": codigo_js("resultado"),
    }


def ejemplos_de_ayuda():
    """Ejemplos REALES: se ejecuta el código del proyecto y se muestra lo que devuelve."""
    base = ArbolABB()
    base.construir([50, 30, 70, 20, 40, 60, 80])

    parcial = ArbolABB()
    parcial.construir([50, 30, 70])
    pasos_20 = parcial.insertar(20)                   # pasos reales de insertar el 20

    pasos_inorden = base.generar_pasos_inorden()      # pasos reales del recorrido

    pequeno = ArbolABB()
    pasos_pequeno = pequeno.construir([50, 30, 70])
    respuesta = {
        "ok": True,
        "valores": [50, 30, 70],
        "arbol": pequeno.a_diccionario(),
        "pasos_insercion": f"[... {len(pasos_pequeno)} pasos ...]",
        "avisos": [],
    }

    degenerado = ArbolABB()
    degenerado.construir([10, 20, 30, 40])

    mala = "50, 30, abc, 3.5"
    valores_mala, errores_mala, avisos_mala = validar_entrada(mala)
    buena = "50 30;70\n20"
    valores_buena, errores_buena, avisos_buena = validar_entrada(buena)
    repetida = "50, 30, 70, 30, 50"
    valores_rep, errores_rep, avisos_rep = validar_entrada(repetida)

    return {
        "insercion": "\n".join(f"{p['tipo']:<9}{p['mensaje']}" for p in pasos_20),
        "paso_json": json.dumps(pasos_20[0], ensure_ascii=False, indent=2),
        "inorden_pasos": "\n".join(f"{i:>2}. {p['tipo']:<8}{p['mensaje']}"
                                   for i, p in enumerate(pasos_inorden[:9], start=1)) + "\n ...",
        "inorden_resultado": " → ".join(str(v) for v in base.inorden()),
        "resumen": f"raiz = {base.raiz.valor}, cantidad = {base.contar_nodos()}, altura = {base.calcular_altura()}",
        "nodos_json": "\n".join(json.dumps(n, ensure_ascii=False) for n in base.obtener_nodos()[:3]) + "\n ...",
        "respuesta_json": json.dumps(respuesta, ensure_ascii=False),
        "validacion_mala": (f'validar_entrada("{mala}")\n  valores  = {valores_mala}\n  avisos   = {avisos_mala}\n  errores  =\n'
                            + "\n".join("    - " + e for e in errores_mala)),
        "validacion_buena": (f"validar_entrada({buena!r})\n  valores  = {valores_buena}\n"
                             f"  avisos   = {avisos_buena}\n  errores  = {errores_buena}"),
        "validacion_repetida": (f'validar_entrada("{repetida}")\n  valores  = {valores_rep}\n  errores  = {errores_rep}\n  avisos   =\n'
                                + "\n".join("    - " + v for v in avisos_rep)),
        "arboles": {"principal": base.obtener_nodos(), "degenerado": degenerado.obtener_nodos()},
    }


if __name__ == "__main__":
    # Servidor local. Abre http://127.0.0.1:5000 en el navegador.
    app.run(host="127.0.0.1", port=5000, debug=False)
