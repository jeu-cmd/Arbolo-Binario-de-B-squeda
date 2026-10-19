# Árbol Binario de Búsqueda (ABB) en Python + Flask

Proyecto final de Matemática Discreta. La **lógica del árbol está escrita en Python**
(inserción, recorrido Inorden, altura, validaciones). El navegador solo dibuja y anima
lo que Python calcula: JavaScript **no** repite ningún algoritmo del ABB.

El resultado ascendente sale del recorrido Inorden del árbol; no se usa `sort()`,
`sorted()` ni ninguna otra función de ordenamiento.

## Instalación y ejecución en Windows

1. Instala Python 3.9 o superior desde <https://www.python.org/downloads/>
   (marca **Add python.exe to PATH** durante la instalación).
2. Descomprime el ZIP y abre una terminal (CMD o PowerShell) dentro de la carpeta del proyecto:
   ```
   cd ruta\a\abb_flask
   ```
3. (Recomendado) crea y activa un entorno virtual:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
   En PowerShell, si bloquea el script: `Set-ExecutionPolicy -Scope Process Bypass` y vuelve a activar.
4. Instala las dependencias (solo Flask; es lo único que necesita Internet):
   ```
   pip install -r requirements.txt
   ```
5. Ejecuta la aplicación:
   ```
   python app.py
   ```
6. Abre en el navegador la dirección que indica Flask: <http://127.0.0.1:5000>

Después de instalar Flask la aplicación funciona **sin conexión a Internet**.
Para detenerla, pulsa `Ctrl + C` en la terminal. Si cambias el código, detén y vuelve a ejecutar.
Si el puerto 5000 está ocupado, cambia `port=5000` al final de `app.py`.

## Cómo usarla

1. Escribe números enteros (separados por comas, espacios, saltos de línea o punto y coma)
   y pulsa **Construir árbol**. Mínimo 2 números distintos; si repites uno, se toma una sola vez.
2. La inserción se anima sola: verás cada comparación (`30 < 50`), la dirección elegida y la
   nueva conexión. Puedes pausar, continuar, ir paso a paso, reiniciar, mostrar el árbol
   completo y cambiar la velocidad.
3. Al terminar la inserción se habilita **Ejecutar Inorden**: el recorrido baja por la izquierda,
   visita el nodo, sube a los padres y va agregando cada valor al resultado.
4. En la barra lateral: **¿Qué es un ABB?** (teoría) y **Ayuda y algoritmos** (el código real
   explicado bloque por bloque, para estudiar y defender el proyecto).

Entrada de prueba del proyecto (escríbela en el campo de texto):

```
50, 30, 70, 20, 40, 60, 80
```
Resultado esperado: `20 → 30 → 40 → 50 → 60 → 70 → 80`.

## Archivos

| Archivo | Contenido |
|---|---|
| `arbol.py` | Clases `Nodo` y `ArbolABB`: `insertar`, `construir`, `buscar`, `inorden`, `generar_pasos_inorden`, `contar_nodos`, `calcular_altura`, `obtener_nodos` |
| `app.py` | Flask: validación de la entrada y rutas JSON |
| `templates/index.html` | Estructura de la interfaz (tres secciones) |
| `static/css/styles.css` | Diseño y colores |
| `static/js/app.js` | Dibujo SVG, controles de animación y comunicación con Flask |
| `pruebas.py` | Pruebas automáticas (`python pruebas.py`) |
| `requirements.txt` | Dependencias (Flask) |

## Rutas de Flask

| Ruta | Qué hace |
|---|---|
| `GET /` | Muestra la interfaz |
| `POST /api/construir` | Valida el texto, construye el ABB y devuelve el árbol y los pasos de inserción |
| `GET /api/inorden` | Devuelve el resultado ascendente (`inorden()`) y los pasos del recorrido |
| `POST /api/reiniciar` | Olvida el árbol actual |

## Validaciones

Se rechazan (con un mensaje claro y sin construir el árbol): entrada vacía, menos de 2 números,
caracteres no numéricos, decimales (como `3.5`) y enteros fuera del rango seguro de JavaScript
(±9007199254740991). Si la entrada es inválida, el árbol que ya estaba construido se conserva.

**Valores repetidos:** no son un error. Se toma uno solo (el primero que aparece, así se respeta el
orden de ingreso) y debajo del campo de texto se avisa cuáles eran. Ejemplo: `50, 30, 70, 30, 50`
construye el árbol con `50, 30, 70`. Si todos los números son iguales (por ejemplo `5, 5`) no se
construye, porque se necesitan al menos 2 números distintos.

## Pruebas

```
python pruebas.py
```
Comprueba el árbol del ejemplo, árboles inclinados, negativos, casos aleatorios (Inorden siempre
ascendente), que los pasos de animación coincidan con `inorden()`, la validación, las rutas, que no
se use ningún ordenamiento predeterminado y que el código mostrado en «Ayuda y algoritmos» exista
realmente en los archivos.

## Nota sobre árboles muy grandes

No hay un máximo fijo de números. Con cientos de números la animación paso a paso es larga:
usa **Mostrar árbol completo**. Un árbol de más de ~900 niveles (por ejemplo, 1000 números ya
ordenados) se rechaza con un mensaje, por el límite de recursión de Python.
