"""
arbol.py - Lógica oficial del Árbol Binario de Búsqueda (ABB)

Todo el algoritmo del proyecto está en este archivo, escrito en Python:
  * insertar un valor (registrando cada comparación para la animación),
  * recorrer el árbol en Inorden: Izquierda -> Raíz -> Derecha,
  * contar nodos y calcular la altura,
  * entregar a la interfaz los datos que necesita para dibujar el árbol.

JavaScript NO repite ninguno de estos algoritmos: solo dibuja lo que Python calcula.
Los números salen en orden ascendente únicamente gracias al recorrido Inorden
del árbol; no se usa ninguna función de ordenamiento del lenguaje.
"""


class Nodo:
    """Un nodo del árbol: guarda un valor y los enlaces a sus dos hijos."""

    def __init__(self, valor):
        self.valor = valor       # número entero que guarda el nodo
        self.izquierdo = None    # hijo izquierdo: aquí van los valores MENORES
        self.derecho = None      # hijo derecho: aquí van los valores MAYORES


class ArbolABB:
    """Árbol Binario de Búsqueda. Solo guarda la raíz; desde ella se llega a todos los nodos."""

    def __init__(self):
        self.raiz = None         # árbol vacío: todavía no hay raíz

    # ------------------------------------------------------------------
    # INSERTAR
    # ------------------------------------------------------------------
    def insertar(self, valor):
        """
        Inserta `valor` respetando la regla del ABB:
            menor -> subárbol izquierdo
            mayor -> subárbol derecho
        Devuelve la lista de pasos que se dieron (la usa la animación del navegador):
            "raiz"     -> el árbol estaba vacío y el valor se convierte en la raíz
            "comparar" -> se comparó el valor con un nodo y se eligió una dirección
            "insertar" -> se encontró un hueco y se creó el nodo nuevo
        """
        pasos = []

        # Caso 1: árbol vacío -> el valor se convierte en la raíz.
        if self.raiz is None:
            self.raiz = Nodo(valor)
            pasos.append({
                "tipo": "raiz",
                "valor": valor,
                "mensaje": f"El árbol está vacío: {valor} se convierte en la raíz.",
            })
            return pasos

        # Caso 2: el árbol ya tiene nodos -> bajamos desde la raíz comparando.
        actual = self.raiz
        while True:
            if valor < actual.valor:
                operador, lado, hijo = "<", "izquierdo", actual.izquierdo
                explicacion = "es menor, así que va a la izquierda"
            elif valor > actual.valor:
                operador, lado, hijo = ">", "derecho", actual.derecho
                explicacion = "es mayor, así que va a la derecha"
            else:
                # Un ABB no admite claves iguales (la validación ya las rechazó antes).
                raise ValueError(f"El valor {valor} ya existe en el árbol.")

            pasos.append({
                "tipo": "comparar",
                "valor": valor,              # número que se está insertando
                "comparado": actual.valor,   # nodo con el que se compara
                "operador": operador,        # "<" o ">"
                "direccion": lado,           # hacia dónde sigue el camino
                "hijo": hijo.valor if hijo is not None else None,  # siguiente nodo del camino
                "mensaje": f"{valor} {operador} {actual.valor}: {explicacion}.",
            })

            if hijo is None:
                # Encontramos un hueco vacío: aquí se crea el nodo nuevo y se enlaza.
                nuevo = Nodo(valor)
                if lado == "izquierdo":
                    actual.izquierdo = nuevo
                else:
                    actual.derecho = nuevo
                pasos.append({
                    "tipo": "insertar",
                    "valor": valor,
                    "padre": actual.valor,
                    "lado": lado,
                    "mensaje": (f"{actual.valor} no tiene hijo {lado}: "
                                f"{valor} se inserta como hijo {lado} de {actual.valor}."),
                })
                return pasos

            actual = hijo    # seguimos bajando por el hijo elegido

    def construir(self, valores):
        """
        Inserta los valores EN EL ORDEN EN QUE LLEGAN (así lo exige el proyecto).
        Devuelve el registro completo de pasos de inserción.
        """
        pasos = []
        for numero_de_valor, valor in enumerate(valores, start=1):
            for paso in self.insertar(valor):
                paso["orden"] = numero_de_valor   # qué valor de la lista se está insertando
                pasos.append(paso)
        pasos.append({
            "tipo": "fin",
            "mensaje": f"Árbol completo: {self.contar_nodos()} nodos y altura {self.calcular_altura()}.",
        })
        return pasos

    # ------------------------------------------------------------------
    # BUSCAR
    # ------------------------------------------------------------------
    def buscar(self, valor):
        """Busca `valor` con la misma regla del ABB. Devuelve True si está en el árbol."""
        actual = self.raiz
        while actual is not None:
            if valor == actual.valor:
                return True
            actual = actual.izquierdo if valor < actual.valor else actual.derecho
        return False

    # ------------------------------------------------------------------
    # RECORRIDO INORDEN: Izquierda -> Raíz -> Derecha
    # ------------------------------------------------------------------
    def inorden(self):
        """Devuelve los valores del árbol en orden ascendente (recorrido Inorden)."""
        resultado = []
        self._inorden(self.raiz, resultado)
        return resultado

    def _inorden(self, nodo, resultado):
        if nodo is None:                           # caso base: subárbol vacío
            return
        self._inorden(nodo.izquierdo, resultado)   # 1) Izquierda
        resultado.append(nodo.valor)               # 2) Raíz (se "visita")
        self._inorden(nodo.derecho, resultado)     # 3) Derecha

    def generar_pasos_inorden(self):
        """
        Genera los eventos del recorrido Inorden para la animación:
            "bajar"   -> llegamos a un nodo (desde su padre; la raíz es el inicio)
            "visitar" -> se visita el nodo: su valor entra en el resultado
            "subir"   -> terminamos el subárbol de un hijo y regresamos a su padre
            "fin"     -> el recorrido terminó
        Sigue el mismo orden que inorden(): Izquierda -> Raíz -> Derecha.
        """
        pasos = []
        self._pasos_inorden(self.raiz, None, None, pasos)
        if self.raiz is None:
            texto = "El árbol está vacío: no hay nada que recorrer."
        else:
            texto = "Recorrido terminado. Resultado ascendente: " + " → ".join(str(v) for v in self.inorden())
        pasos.append({"tipo": "fin", "mensaje": texto})
        return pasos

    def _pasos_inorden(self, nodo, padre, lado, pasos):
        if nodo is None:                           # caso base: no hay subárbol
            return

        # Llegamos a este nodo (desde su padre; la raíz no tiene padre).
        if padre is None:
            texto = (f"Empezamos en la raíz ({nodo.valor}). "
                     "Regla: primero la izquierda, luego la raíz y al final la derecha.")
        else:
            direccion = "izquierda" if lado == "izquierdo" else "derecha"
            texto = f"Desde {padre.valor} bajamos por la {direccion} hasta {nodo.valor}."
        pasos.append({
            "tipo": "bajar",
            "valor": nodo.valor,
            "padre": padre.valor if padre is not None else None,
            "lado": lado,
            "mensaje": texto,
        })

        # 1) IZQUIERDA: se recorre todo el subárbol izquierdo antes de visitar este nodo.
        self._pasos_inorden(nodo.izquierdo, nodo, "izquierdo", pasos)
        if nodo.izquierdo is not None:
            pasos.append({
                "tipo": "subir",
                "valor": nodo.valor,
                "desde": nodo.izquierdo.valor,
                "mensaje": f"Terminamos el subárbol de {nodo.izquierdo.valor}: regresamos a su padre {nodo.valor}.",
            })

        # 2) RAÍZ: se visita el nodo y su valor se agrega al resultado.
        if nodo.izquierdo is None:
            motivo = f"{nodo.valor} no tiene hijo izquierdo"
        else:
            motivo = f"Ya recorrimos el subárbol izquierdo de {nodo.valor}"
        pasos.append({
            "tipo": "visitar",
            "valor": nodo.valor,
            "mensaje": f"{motivo}: se visita {nodo.valor} y se agrega al resultado.",
        })

        # 3) DERECHA: se recorre el subárbol derecho.
        self._pasos_inorden(nodo.derecho, nodo, "derecho", pasos)
        if nodo.derecho is not None:
            pasos.append({
                "tipo": "subir",
                "valor": nodo.valor,
                "desde": nodo.derecho.valor,
                "mensaje": f"Terminamos el subárbol de {nodo.derecho.valor}: regresamos a su padre {nodo.valor}.",
            })

    # ------------------------------------------------------------------
    # CÁLCULOS DEL ÁRBOL
    # ------------------------------------------------------------------
    def contar_nodos(self):
        """Cantidad de nodos del árbol."""
        return self._contar(self.raiz)

    def _contar(self, nodo):
        if nodo is None:
            return 0
        return 1 + self._contar(nodo.izquierdo) + self._contar(nodo.derecho)

    def calcular_altura(self):
        """Altura = número de niveles (un árbol con solo la raíz tiene altura 1; vacío, 0)."""
        return self._altura(self.raiz)

    def _altura(self, nodo):
        if nodo is None:
            return 0
        return 1 + max(self._altura(nodo.izquierdo), self._altura(nodo.derecho))

    # ------------------------------------------------------------------
    # DATOS PARA DIBUJAR EL ÁRBOL
    # ------------------------------------------------------------------
    def obtener_nodos(self):
        """
        Lista con los datos que el navegador necesita para dibujar cada nodo:
            valor    -> el número del nodo
            nivel    -> profundidad (la raíz es 0, sus hijos 1, ...)
            posicion -> columna horizontal = lugar del nodo en el recorrido Inorden
            padre    -> valor del nodo padre (None en la raíz)
            lado     -> "izquierdo" o "derecho" según de qué hijo se trate
        """
        nodos = []
        self._recolectar(self.raiz, 0, None, None, nodos)
        return nodos

    def _recolectar(self, nodo, nivel, padre, lado, nodos):
        if nodo is None:
            return
        self._recolectar(nodo.izquierdo, nivel + 1, nodo.valor, "izquierdo", nodos)
        # Todos los nodos de la izquierda ya están en la lista: esa cantidad es su columna.
        nodos.append({
            "valor": nodo.valor,
            "nivel": nivel,
            "posicion": len(nodos),
            "padre": padre,
            "lado": lado,
        })
        self._recolectar(nodo.derecho, nivel + 1, nodo.valor, "derecho", nodos)

    def a_diccionario(self):
        """Resumen del árbol listo para enviarlo como JSON a la interfaz."""
        return {
            "raiz": self.raiz.valor if self.raiz is not None else None,
            "cantidad": self.contar_nodos(),
            "altura": self.calcular_altura(),
            "nodos": self.obtener_nodos(),
        }
