import ast
import html
import random
import re
import unittest
from pathlib import Path

from app import app, codigo_de_ayuda, estado, validar_entrada
from arbol import ArbolABB

CARPETA = Path(__file__).resolve().parent
EJEMPLO = [50, 30, 70, 20, 40, 60, 80]


def arbol_con(valores):
    arbol = ArbolABB()
    arbol.construir(valores)
    return arbol


def forma(nodo):
    """Estructura del árbol como tuplas anidadas: (valor, izquierdo, derecho)."""
    if nodo is None:
        return None
    return (nodo.valor, forma(nodo.izquierdo), forma(nodo.derecho))


class PruebasDelArbol(unittest.TestCase):

    def test_ejemplo_del_proyecto(self):
        arbol = arbol_con(EJEMPLO)
        esperado = (50, (30, (20, None, None), (40, None, None)),
                        (70, (60, None, None), (80, None, None)))
        self.assertEqual(forma(arbol.raiz), esperado)
        self.assertEqual(arbol.inorden(), [20, 30, 40, 50, 60, 70, 80])
        self.assertEqual(arbol.contar_nodos(), 7)
        self.assertEqual(arbol.calcular_altura(), 3)

    def test_se_respeta_el_orden_de_ingreso(self):
        self.assertEqual(forma(arbol_con([30, 50, 70]).raiz), (30, None, (50, None, (70, None, None))))
        self.assertEqual(forma(arbol_con([70, 50, 30]).raiz), (70, (50, (30, None, None), None), None))
        self.assertEqual(forma(arbol_con([50, 30, 70]).raiz), (50, (30, None, None), (70, None, None)))

    def test_arboles_inclinados(self):
        derecha = arbol_con([1, 2, 3, 4, 5, 6])
        izquierda = arbol_con([6, 5, 4, 3, 2, 1])
        for arbol in (derecha, izquierda):
            self.assertEqual(arbol.inorden(), [1, 2, 3, 4, 5, 6])
            self.assertEqual(arbol.calcular_altura(), 6)

    def test_numeros_negativos_y_cero(self):
        arbol = arbol_con([0, -5, 5, -10, 10, -1])
        self.assertEqual(arbol.inorden(), [-10, -5, -1, 0, 5, 10])

    def test_inorden_es_ascendente_en_casos_aleatorios(self):
        azar = random.Random(7)
        for _ in range(200):
            entrada = azar.sample(range(-500, 500), azar.randint(2, 40))
            arbol = arbol_con(entrada)
            resultado = arbol.inorden()
            self.assertEqual(len(resultado), len(entrada))
            self.assertEqual(set(resultado), set(entrada))
            self.assertTrue(all(a < b for a, b in zip(resultado, resultado[1:])))
            self.assertTrue(all(arbol.buscar(v) for v in entrada))
            self.assertFalse(arbol.buscar(1000))

    def test_pasos_de_insercion(self):
        arbol = ArbolABB()
        pasos = arbol.construir([50, 30, 70, 20])
        resumen = [(p["tipo"], p.get("valor"), p.get("comparado"), p.get("operador")) for p in pasos]
        self.assertEqual(resumen, [
            ("raiz", 50, None, None),
            ("comparar", 30, 50, "<"), ("insertar", 30, None, None),
            ("comparar", 70, 50, ">"), ("insertar", 70, None, None),
            ("comparar", 20, 50, "<"), ("comparar", 20, 30, "<"), ("insertar", 20, None, None),
            ("fin", None, None, None),
        ])
        self.assertEqual(pasos[2]["padre"], 50)
        self.assertEqual(pasos[2]["lado"], "izquierdo")
        self.assertEqual([p["orden"] for p in pasos[:-1]], [1, 2, 2, 3, 3, 4, 4, 4])

    def test_cada_valor_aparece_una_sola_vez(self):
        pasos = ArbolABB().construir(EJEMPLO)
        creados = [p["valor"] for p in pasos if p["tipo"] in ("raiz", "insertar")]
        self.assertEqual(creados, EJEMPLO)

    def test_pasos_de_inorden_coinciden_con_inorden(self):
        azar = random.Random(11)
        casos = [EJEMPLO, [1, 2, 3, 4], [4, 3, 2, 1], [5, 1]]
        casos += [azar.sample(range(-100, 100), azar.randint(2, 30)) for _ in range(50)]
        for entrada in casos:
            arbol = arbol_con(entrada)
            pasos = arbol.generar_pasos_inorden()
            visitados = [p["valor"] for p in pasos if p["tipo"] == "visitar"]
            self.assertEqual(visitados, arbol.inorden())
            n = len(entrada)
            tipos = [p["tipo"] for p in pasos]
            self.assertEqual((tipos.count("bajar"), tipos.count("visitar"), tipos.count("subir"), tipos[-1]),
                             (n, n, n - 1, "fin"))

    def test_los_pasos_de_inorden_son_un_camino_valido(self):
        arbol = arbol_con(EJEMPLO)
        actual = None
        for paso in arbol.generar_pasos_inorden():
            if paso["tipo"] == "bajar":
                self.assertEqual(paso["padre"], actual)       # solo se baja desde el padre
                actual = paso["valor"]
            elif paso["tipo"] == "visitar":
                self.assertEqual(paso["valor"], actual)       # se visita el nodo donde estamos
            elif paso["tipo"] == "subir":
                self.assertEqual(paso["desde"], actual)       # se sube desde el hijo donde terminamos
                actual = paso["valor"]

    def test_arbol_vacio(self):
        arbol = ArbolABB()
        self.assertEqual(arbol.inorden(), [])
        self.assertEqual([p["tipo"] for p in arbol.generar_pasos_inorden()], ["fin"])
        self.assertEqual((arbol.contar_nodos(), arbol.calcular_altura()), (0, 0))

    def test_un_repetido_en_el_arbol_da_error(self):
        arbol = arbol_con([5, 3])
        with self.assertRaises(ValueError):
            arbol.insertar(3)

    def test_posiciones_para_dibujar(self):
        nodos = arbol_con(EJEMPLO).obtener_nodos()
        self.assertEqual([n["valor"] for n in nodos], [20, 30, 40, 50, 60, 70, 80])
        self.assertEqual([n["posicion"] for n in nodos], [0, 1, 2, 3, 4, 5, 6])
        self.assertEqual([n["nivel"] for n in nodos], [2, 1, 2, 0, 2, 1, 2])
        self.assertEqual({n["valor"]: n["padre"] for n in nodos}[20], 30)


class PruebasDeValidacion(unittest.TestCase):

    def test_entrada_correcta_y_separadores(self):
        self.assertEqual(validar_entrada("50, 30, 70, 20, 40, 60, 80"), (EJEMPLO, [], []))
        self.assertEqual(validar_entrada("50 30;70\n20,40"), ([50, 30, 70, 20, 40], [], []))
        self.assertEqual(validar_entrada("-5, +3, 0"), ([-5, 3, 0], [], []))

    def test_entrada_vacia(self):
        for texto in ("", "   ", ",;\n"):
            _, errores, _ = validar_entrada(texto)
            self.assertTrue(errores and "vacía" in errores[0])

    def test_menos_de_dos_numeros(self):
        _, errores, _ = validar_entrada("5")
        self.assertTrue(any("al menos 2" in e for e in errores))

    def test_caracteres_no_numericos(self):
        _, errores, _ = validar_entrada("abc, 5, 6x")
        self.assertTrue(any("abc" in e and "6x" in e for e in errores))

    def test_decimales(self):
        _, errores, _ = validar_entrada("3.5, 4, 5")
        self.assertTrue(any("decimales" in e and "3.5" in e for e in errores))

    def test_valores_repetidos_se_toma_uno_solo(self):
        valores, errores, avisos = validar_entrada("1, 1, 2, 007, 7")
        self.assertEqual(valores, [1, 2, 7])          # uno solo, en orden de primera aparición
        self.assertEqual(errores, [])
        self.assertTrue(any("1 (2 veces)" in a and "7 (2 veces)" in a for a in avisos))
        self.assertEqual(validar_entrada("50, 30, 70, 30, 50")[0], [50, 30, 70])

    def test_si_todos_son_iguales_faltan_numeros_distintos(self):
        _, errores, _ = validar_entrada("5, 5, 5")
        self.assertTrue(any("distintos" in e for e in errores))

    def test_rango_seguro_de_javascript(self):
        self.assertEqual(validar_entrada("9007199254740991, -9007199254740991"), ([9007199254740991, -9007199254740991], [], []))
        _, errores, _ = validar_entrada("9007199254740992, 1")
        self.assertTrue(any("rango seguro" in e and "9007199254740992" in e for e in errores))
        _, errores, _ = validar_entrada("9" * 5000 + ", 1")
        self.assertTrue(any("rango seguro" in e for e in errores))

    def test_varios_errores_a_la_vez(self):
        valores, errores, avisos = validar_entrada("50, 30, abc, 3.5, 30")
        self.assertEqual(len(errores), 2)             # no numérico y decimal
        self.assertEqual(valores, [50, 30])
        self.assertEqual(len(avisos), 1)


class PruebasDeLaApi(unittest.TestCase):

    def setUp(self):
        estado["arbol"] = None
        self.cliente = app.test_client()

    def construir(self, texto):
        return self.cliente.post("/api/construir", json={"texto": texto})

    def test_construir_el_ejemplo(self):
        respuesta = self.construir("50, 30, 70, 20, 40, 60, 80")
        datos = respuesta.get_json()
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(datos["ok"])
        self.assertEqual(datos["valores"], EJEMPLO)
        self.assertEqual((datos["arbol"]["raiz"], datos["arbol"]["cantidad"], datos["arbol"]["altura"]), (50, 7, 3))
        self.assertEqual(datos["pasos_insercion"][-1]["tipo"], "fin")

    def test_repetidos_en_la_api_se_toma_uno_solo(self):
        datos = self.construir("5, 3, 5, 8, 3").get_json()
        self.assertTrue(datos["ok"])
        self.assertEqual(datos["valores"], [5, 3, 8])
        self.assertTrue(datos["avisos"])
        self.assertEqual(datos["arbol"]["cantidad"], 3)
        self.assertEqual(self.cliente.get("/api/inorden").get_json()["resultado"], [3, 5, 8])

    def test_inorden_pide_primero_un_arbol(self):
        self.assertEqual(self.cliente.get("/api/inorden").status_code, 409)

    def test_inorden_del_ejemplo(self):
        self.construir("50, 30, 70, 20, 40, 60, 80")
        datos = self.cliente.get("/api/inorden").get_json()
        self.assertTrue(datos["ok"])
        self.assertEqual(datos["resultado"], [20, 30, 40, 50, 60, 70, 80])
        self.assertEqual([p["valor"] for p in datos["pasos"] if p["tipo"] == "visitar"], datos["resultado"])
        self.assertEqual(datos["pasos"][-1]["tipo"], "fin")

    def test_entrada_invalida_no_construye_ni_cambia_el_arbol(self):
        self.construir("5, 3, 8")
        respuesta = self.construir("5, abc")
        self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(respuesta.get_json()["ok"])
        self.assertEqual(self.cliente.get("/api/inorden").get_json()["resultado"], [3, 5, 8])

    def test_primera_entrada_invalida_deja_el_servidor_sin_arbol(self):
        self.assertEqual(self.construir("5").status_code, 400)
        self.assertEqual(self.cliente.get("/api/inorden").status_code, 409)

    def test_reconstrucciones_consecutivas(self):
        self.construir("3, 1, 2")
        self.construir("10, 20, 15, 5")
        self.assertEqual(self.cliente.get("/api/inorden").get_json()["resultado"], [5, 10, 15, 20])

    def test_reiniciar(self):
        self.construir("3, 1, 2")
        self.assertTrue(self.cliente.post("/api/reiniciar").get_json()["ok"])
        self.assertEqual(self.cliente.get("/api/inorden").status_code, 409)

    def test_cuerpo_que_no_es_json(self):
        respuesta = self.cliente.post("/api/construir", data="hola", content_type="text/plain")
        self.assertEqual(respuesta.status_code, 400)

    def test_arbol_demasiado_profundo_da_un_mensaje_claro(self):
        respuesta = self.construir(", ".join(str(n) for n in range(1500)))
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("profundo", respuesta.get_json()["errores"][0])

    def test_la_pagina_se_muestra_con_el_codigo_real(self):
        pagina = self.cliente.get("/").get_data(as_text=True)
        self.assertIn("self.izquierdo = None", pagina)
        self.assertIn("class Reproductor", pagina)
        self.assertNotIn("bloque no encontrado", pagina)


class PruebasDeRestriccionesYAyuda(unittest.TestCase):

    def test_no_se_usan_funciones_de_ordenamiento(self):
        for nombre in ("arbol.py", "app.py", "pruebas.py"):
            arbol_sintactico = ast.parse((CARPETA / nombre).read_text(encoding="utf-8"))
            for nodo in ast.walk(arbol_sintactico):
                if isinstance(nodo, ast.Call):
                    funcion = nodo.func
                    llamada = funcion.attr if isinstance(funcion, ast.Attribute) else getattr(funcion, "id", "")
                    self.assertNotIn(llamada, ("sort", "sorted"), f"{nombre} usa {llamada}()")
        js = (CARPETA / "static" / "js" / "app.js").read_text(encoding="utf-8")
        self.assertNotRegex(js, r"\.sort\(|\bsorted\(")

    def test_el_codigo_de_la_ayuda_se_lee_de_los_archivos(self):
        for clave, texto in codigo_de_ayuda().items():
            self.assertTrue(texto.strip(), clave)
            self.assertNotIn("bloque no encontrado", texto, clave)

    def test_fragmentos_explicados_existen_en_el_codigo_real(self):
        fuentes = "".join((CARPETA / ruta).read_text(encoding="utf-8")
                          for ruta in ("arbol.py", "app.py", "static/js/app.js"))
        plantilla = (CARPETA / "templates" / "index.html").read_text(encoding="utf-8")
        explicados = []
        for lista in re.findall(r'<ul class="lineas">(.*?)</ul>', plantilla, re.S):
            explicados += [html.unescape(f) for f in re.findall(r'<li><code>(.*?)</code>', lista)]
        self.assertGreater(len(explicados), 50)
        for fragmento in explicados:
            self.assertIn(fragmento, fuentes, f"No existe en el código: {fragmento}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
