"use strict";

/* ==========================================================================
   app.js - Interfaz del Árbol Binario de Búsqueda

   Este archivo NO implementa el árbol. Le pide a Python (Flask) los datos y los
   pasos de inserción / recorrido, y se limita a:
     1) dibujar esos datos con SVG,
     2) controlar la reproducción de las animaciones,
     3) mostrar mensajes y resultados.
   ========================================================================== */

const $ = (id) => document.getElementById(id);
const SVG_NS = "http://www.w3.org/2000/svg";

// Referencias a elementos de la página.
const el = {
  entrada: $("entrada"),
  btnConstruir: $("btn-construir"),
  btnLimpiar: $("btn-limpiar"),
  pista: $("pista"),
  alerta: $("alerta"),
  alertaLista: $("alerta-lista"),
  alertaCerrar: $("alerta-cerrar"),
  chipEstado: $("chip-estado"),
  estadoTexto: $("estado-texto"),
  topNodos: $("top-nodos"),
  svg: $("svg-arbol"),
  lienzo: $("lienzo"),
  vacio: $("arbol-vacio"),
  aviso: $("aviso"),
  mRaiz: $("m-raiz"),
  mNodos: $("m-nodos"),
  mAltura: $("m-altura"),
  resInorden: $("res-inorden"),
  resEstado: $("res-estado"),
  resComparacion: $("res-comparacion"),
  resMensaje: $("res-mensaje"),
};

// Lo que la interfaz recuerda del árbol actual (todo viene de Python).
const modelo = {
  arbol: null,            // { raiz, cantidad, altura, nodos } calculado por Python
  dibujo: null,           // medidas y elementos SVG (resultado de dibujarArbol)
  pasosInsercion: [],     // pasos de inserción generados por Python
  aparicion: new Map(),   // valor -> número del paso en el que aparece su nodo
  pasosInorden: [],       // pasos del recorrido Inorden (se piden a Python)
  resultado: [],          // resultado de inorden() calculado por Python
  version: 0,             // sube con cada árbol nuevo: sirve para descartar respuestas viejas
  inordenPedido: -1,      // versión para la que ya se pidieron los pasos de Inorden
  hayError: false,
};

const PISTA_INICIAL = el.pista.textContent;

// Mensaje bajo el campo de texto: la pista normal o un aviso (por ejemplo, repetidos ignorados).
function ponerPista(avisos) {
  el.pista.textContent = avisos.length ? avisos.join(" ") : PISTA_INICIAL;
  el.pista.classList.toggle("con-aviso", avisos.length > 0);
}

function crearSVG(nombre, atributos = {}, clase = "") {
  const nodo = document.createElementNS(SVG_NS, nombre);
  for (const [clave, valor] of Object.entries(atributos)) nodo.setAttribute(clave, valor);
  if (clase) nodo.setAttribute("class", clase);
  return nodo;
}

/* ==========================================================================
   1) DIBUJO DEL ÁRBOL EN SVG
   ========================================================================== */

// [AYUDA: dibujo]
const ALTO_NODO = 34;        // alto de cada nodo (unidades del SVG)
const SEP_VERTICAL = 62;     // distancia entre un nivel y el siguiente
const MARGEN = 26;           // espacio libre alrededor del árbol

function anchoDeNodo(valor) {
  return Math.max(ALTO_NODO, String(valor).length * 9 + 16);   // los números largos ensanchan el nodo
}

function dibujarArbol(svg, nodos) {
  svg.replaceChildren();                         // borra el dibujo anterior
  const capaAristas = crearSVG("g");
  const capaNodos = crearSVG("g");
  svg.append(capaAristas, capaNodos);            // las aristas quedan DEBAJO de los nodos

  const anchoMax = nodos.reduce((m, n) => Math.max(m, anchoDeNodo(n.valor)), ALTO_NODO);
  const sepH = Math.max(46, anchoMax + 10);      // distancia horizontal entre columnas
  const maxNivel = nodos.reduce((m, n) => Math.max(m, n.nivel), 0);

  // 1) Coordenadas: la columna (posicion) y el nivel los calculó Python.
  const vista = new Map();
  for (const n of nodos) {
    n.x = MARGEN + anchoMax / 2 + n.posicion * sepH;
    n.y = MARGEN + ALTO_NODO / 2 + n.nivel * SEP_VERTICAL;
    vista.set(n.valor, { nodo: n });
  }

  // 2) Aristas: una línea desde cada padre hasta su hijo.
  for (const n of nodos) {
    if (n.padre === null) continue;              // la raíz no tiene padre
    const p = vista.get(n.padre).nodo;
    const linea = crearSVG("line", { x1: p.x, y1: p.y, x2: n.x, y2: n.y }, "arista");
    linea.style.setProperty("--largo", Math.hypot(n.x - p.x, n.y - p.y));
    capaAristas.append(linea);
    vista.get(n.valor).arista = linea;
  }

  // 3) Nodos: un rectángulo redondeado con el número dentro.
  for (const n of nodos) {
    const ancho = anchoDeNodo(n.valor);
    const grupo = crearSVG("g", { transform: `translate(${n.x} ${n.y})` });
    const visual = crearSVG("g", {}, "nodo");
    const forma = crearSVG("rect", {
      x: -ancho / 2, y: -ALTO_NODO / 2, width: ancho, height: ALTO_NODO, rx: ALTO_NODO / 2,
    }, "forma");
    const texto = crearSVG("text", {}, "numero");
    texto.textContent = n.valor;
    visual.append(forma, texto);
    grupo.append(visual);
    capaNodos.append(grupo);
    vista.get(n.valor).visual = visual;
  }

  const ancho = 2 * MARGEN + anchoMax + (nodos.length - 1) * sepH;
  const alto = 2 * MARGEN + ALTO_NODO + maxNivel * SEP_VERTICAL;
  svg.setAttribute("viewBox", `0 0 ${ancho} ${alto}`);
  return { ancho, alto, vista };
}
// [/AYUDA]

// Hace visibles todos los nodos y aristas (sin animación de aparición).
function mostrarTodo(dibujo) {
  for (const v of dibujo.vista.values()) {
    v.visual.classList.add("visible");
    if (v.arista) v.arista.classList.add("visible");
  }
}

// Ajusta el tamaño del SVG al espacio disponible; si el árbol es muy grande, el lienzo tiene su propio scroll.
function ajustarEscala() {
  const dibujo = modelo.dibujo;
  if (!dibujo || el.lienzo.clientWidth === 0) return;
  let escala = Math.min((el.lienzo.clientWidth - 8) / dibujo.ancho, (el.lienzo.clientHeight - 8) / dibujo.alto, 1.8);
  escala = Math.max(escala, 0.7);
  el.svg.style.width = `${dibujo.ancho * escala}px`;
  el.svg.style.height = `${dibujo.alto * escala}px`;
}

/* ==========================================================================
   2) REPRODUCTOR DE ANIMACIONES (sirve para la inserción y para el Inorden)
   ========================================================================== */

// [AYUDA: reproductor]
class Reproductor {
  constructor({ retardo, alMostrar, alCambiar }) {
    this.retardo = retardo;       // función que devuelve los milisegundos entre pasos
    this.alMostrar = alMostrar;   // función que dibuja el paso número k
    this.alCambiar = alCambiar;   // función que actualiza botones y textos
    this.total = 0;               // cantidad de pasos cargados
    this.indice = -1;             // paso que se está mostrando (-1 = todavía ninguno)
    this.estado = "vacio";        // vacio | detenido | reproduciendo | pausado | completo
    this.temporizador = null;     // el setTimeout que programa el siguiente paso
    this.generacion = 0;          // cambia al cargar pasos nuevos: invalida temporizadores viejos
  }

  cargar(total) {
    this.parar();
    this.generacion++;
    this.total = total;
    this.indice = -1;
    this.estado = total > 0 ? "detenido" : "vacio";
    this.alMostrar(this.indice);
    this.alCambiar(this);
  }

  parar() {                       // cancela el paso programado (si lo hay)
    clearTimeout(this.temporizador);
    this.temporizador = null;
  }

  reproducir() {                  // empieza desde el primer paso
    if (this.total === 0) return;
    this.parar();
    this.indice = 0;
    this.alMostrar(this.indice);
    this.estado = this.total > 1 ? "reproduciendo" : "completo";
    if (this.estado === "reproduciendo") this.programar();
    this.alCambiar(this);
  }

  pausar() {
    if (this.estado !== "reproduciendo") return;
    this.parar();
    this.estado = "pausado";
    this.alCambiar(this);
  }

  continuar() {
    if (this.estado !== "pausado") return;
    this.estado = "reproduciendo";
    this.programar();
    this.alCambiar(this);
  }

  siguiente() {
    if (this.total === 0 || this.indice >= this.total - 1) return;
    this.parar();
    this.irA(this.indice + 1);
  }

  anterior() {
    if (this.total === 0 || this.indice < 0) return;
    this.parar();
    this.irA(this.indice - 1);
  }

  reiniciar() {
    if (this.total === 0) return;
    this.parar();
    this.irA(-1);
  }

  mostrarTodo() {
    if (this.total === 0) return;
    this.parar();
    this.irA(this.total - 1);
  }

  irA(indice) {                   // salta a un paso y deja la animación en pausa
    this.indice = indice;
    this.alMostrar(indice);
    if (indice >= this.total - 1) this.estado = "completo";
    else this.estado = indice < 0 ? "detenido" : "pausado";
    this.alCambiar(this);
  }

  programar() {                   // pide avanzar un paso cuando pase el tiempo elegido
    const generacion = this.generacion;
    this.temporizador = setTimeout(() => {
      if (generacion !== this.generacion || this.estado !== "reproduciendo") return;
      this.indice++;
      this.alMostrar(this.indice);
      if (this.indice >= this.total - 1) this.estado = "completo";
      else this.programar();
      this.alCambiar(this);
    }, this.retardo());
  }
}
// [/AYUDA]

/* ==========================================================================
   3) CÓMO SE VE CADA PASO (solo interpreta lo que generó Python)
   ========================================================================== */

function ponerMensaje(texto) {
  el.resMensaje.textContent = texto;
}

// Etiquetas de colores sobre el lienzo (qué valor se inserta, con qué se compara...).
function ponerAviso(chips) {
  el.aviso.replaceChildren(...chips.map((c) => {
    const chip = document.createElement("span");
    chip.className = `chip chip-${c.clase}`;
    chip.textContent = c.texto;
    return chip;
  }));
  el.aviso.hidden = chips.length === 0;
}

function nombreDeLado(lado) {
  return lado === "izquierdo" ? "izquierda" : "derecha";
}

function ponerMetricas(visibles, completo) {
  const a = modelo.arbol;
  const raiz = visibles.find((n) => n.nivel === 0);
  el.mRaiz.textContent = completo ? a.raiz : (raiz ? raiz.valor : "—");
  el.mNodos.textContent = completo ? a.cantidad : visibles.length;
  el.mAltura.textContent = completo ? a.altura : visibles.reduce((m, n) => Math.max(m, n.nivel + 1), 0);
  el.topNodos.textContent = completo ? a.cantidad : visibles.length;
}

function mostrarInsercion(k) {
  const dibujo = modelo.dibujo;
  if (!dibujo) return;
  const pasos = modelo.pasosInsercion;
  const paso = k >= 0 ? pasos[k] : null;

  // Camino que ya recorrió el valor que se inserta: los nodos con los que se comparó.
  const camino = new Set();
  if (paso && paso.tipo !== "fin") {
    for (let j = k; j >= 0 && pasos[j].orden === paso.orden; j--) {
      if (pasos[j].tipo === "comparar") camino.add(pasos[j].comparado);
    }
  }
  const comparando = paso && paso.tipo === "comparar" ? paso.comparado : null;
  const elegida = paso && paso.tipo === "comparar" ? paso.hijo : null;
  const nuevo = paso && (paso.tipo === "insertar" || paso.tipo === "raiz") ? paso.valor : null;

  for (const [valor, v] of dibujo.vista) {
    const visible = modelo.aparicion.get(valor) <= k;      // el nodo aparece cuando llega su paso
    const c = v.visual.classList;
    c.remove("visitando", "cursor", "visitado", "pendiente");   // clases del recorrido Inorden
    c.toggle("visible", visible);
    c.toggle("comparando", valor === comparando);
    c.toggle("camino", visible && valor !== comparando && camino.has(valor));
    c.toggle("nuevo", valor === nuevo);
    if (v.arista) {
      const a = v.arista.classList;
      a.remove("bajada", "subida");
      a.toggle("visible", visible);
      a.toggle("camino", visible && camino.has(valor));
      a.toggle("elegida", visible && valor === elegida);
      a.toggle("nueva", valor === nuevo);
    }
  }

  // Indicadores del árbol con los nodos que ya aparecieron.
  const visibles = modelo.arbol.nodos.filter((n) => modelo.aparicion.get(n.valor) <= k);
  ponerMetricas(visibles, k >= pasos.length - 1);

  // Última comparación realizada hasta este paso.
  let ultima = null;
  for (let j = k; j >= 0; j--) {
    if (pasos[j].tipo === "comparar") { ultima = pasos[j]; break; }
  }
  el.resComparacion.textContent = ultima
    ? `${ultima.valor} ${ultima.operador} ${ultima.comparado} → ${nombreDeLado(ultima.direccion)}`
    : "—";

  // Etiquetas sobre el árbol y mensaje explicativo.
  if (!paso || paso.tipo === "fin") {
    ponerAviso([]);
  } else {
    const chips = [{ clase: "nuevo", texto: `Insertando ${paso.valor} (${paso.orden} de ${modelo.arbol.cantidad})` }];
    if (paso.tipo === "comparar") {
      chips.push({ clase: "compara", texto: `${paso.valor} ${paso.operador} ${paso.comparado} → ${nombreDeLado(paso.direccion)}` });
    } else if (paso.tipo === "insertar") {
      chips.push({ clase: "conexion", texto: `Nueva conexión: ${paso.padre} → ${paso.valor}` });
    }
    ponerAviso(chips);
  }
  ponerMensaje(paso ? paso.mensaje : "Árbol vacío: pulsa «Reproducir» o «Siguiente paso» para ver cómo se inserta cada número.");
}

// [AYUDA: resultado]
function textoSecuencia(valores) {
  return valores.join(" → ");              // 20 → 30 → 40 ...
}

function valoresVisitados(pasos, k) {
  // Solo entran los valores de los pasos "visitar" que ya ocurrieron (del 0 al k).
  const lista = [];
  for (let i = 0; i <= k; i++) {
    if (pasos[i].tipo === "visitar") lista.push(pasos[i].valor);
  }
  return lista;
}
// [/AYUDA]

function mostrarInorden(k) {
  const dibujo = modelo.dibujo;
  if (!dibujo) return;
  const pasos = modelo.pasosInorden;
  const paso = k >= 0 && k < pasos.length ? pasos[k] : null;
  const visitados = paso ? valoresVisitados(pasos, k) : [];
  const yaVisitados = new Set(visitados);
  const visitando = paso && paso.tipo === "visitar" ? paso.valor : null;
  const cursor = paso && (paso.tipo === "bajar" || paso.tipo === "subir") ? paso.valor : null;

  for (const [valor, v] of dibujo.vista) {
    const c = v.visual.classList;
    c.remove("comparando", "camino", "nuevo");                 // clases de la inserción
    c.add("visible");
    c.toggle("visitando", valor === visitando);
    c.toggle("cursor", valor === cursor);
    c.toggle("visitado", paso !== null && yaVisitados.has(valor) && valor !== visitando);
    c.toggle("pendiente", paso !== null && !yaVisitados.has(valor));
    if (v.arista) {
      const a = v.arista.classList;
      a.remove("camino", "elegida", "nueva");
      a.add("visible");
      a.toggle("bajada", paso !== null && paso.tipo === "bajar" && valor === paso.valor);
      a.toggle("subida", paso !== null && paso.tipo === "subir" && valor === paso.desde);
    }
  }

  // Resultado que va creciendo; al final se muestra exactamente lo que devolvió inorden() en Python.
  const final = paso !== null && paso.tipo === "fin";
  el.resInorden.textContent = visitados.length ? textoSecuencia(final ? modelo.resultado : visitados) : "—";

  if (paso === null) {
    ponerAviso([]);
    if (insercion.estado === "completo") {          // si la inserción sigue en curso, el mensaje lo pone ella
      ponerMensaje("Árbol completo. Pulsa «Ejecutar Inorden» para recorrerlo y obtener los números en orden ascendente.");
    }
  } else if (final) {
    ponerAviso([{ clase: "visita", texto: "Recorrido Inorden completo" }]);
    ponerMensaje(paso.mensaje);
  } else {
    const accion = { bajar: "Bajamos a", visitar: "Visitamos", subir: "Regresamos a" }[paso.tipo];
    ponerAviso([{ clase: "visita", texto: `Inorden: ${accion} ${paso.valor}` }]);
    ponerMensaje(paso.mensaje);
  }
}

/* ==========================================================================
   4) PANELES DE CONTROL Y ESTADOS
   ========================================================================== */

const ETIQUETAS = { vacio: "Sin datos", detenido: "Listo", reproduciendo: "Reproduciendo", pausado: "En pausa", completo: "Completo" };
const TONOS = { vacio: "neutro", detenido: "neutro", reproduciendo: "activo", pausado: "aviso", completo: "ok" };

function actualizarPanel(prefijo, rep, habilitado, textoBloqueado) {
  const boton = (nombre) => $(`${prefijo}-${nombre}`);
  const hay = habilitado && rep.total > 0;
  boton("reproducir").disabled = !hay || rep.estado === "reproduciendo";
  boton("pausar").disabled = !hay || rep.estado !== "reproduciendo";
  boton("continuar").disabled = !hay || rep.estado !== "pausado";
  boton("anterior").disabled = !hay || rep.indice < 0;
  boton("siguiente").disabled = !hay || rep.indice >= rep.total - 1;
  boton("reiniciar").disabled = !hay || (rep.indice < 0 && rep.estado !== "reproduciendo");
  boton("completo").disabled = !hay || rep.indice >= rep.total - 1;

  const pildora = $(`${prefijo}-pildora`);
  pildora.textContent = habilitado ? ETIQUETAS[rep.estado] : textoBloqueado;
  pildora.dataset.tono = habilitado ? TONOS[rep.estado] : "neutro";

  const hechos = habilitado ? Math.max(rep.indice + 1, 0) : 0;
  $(`${prefijo}-paso`).textContent = rep.total > 0 ? `Paso ${hechos} de ${rep.total}` : "Sin pasos";
  $(`${prefijo}-barra`).style.width = rep.total > 0 ? `${(hechos / rep.total) * 100}%` : "0%";
}

function actualizarEstadoRecorrido(rep) {
  const total = modelo.arbol ? modelo.arbol.cantidad : 0;
  const visitados = rep.indice >= 0 ? valoresVisitados(modelo.pasosInorden, rep.indice).length : 0;
  const texto = { reproduciendo: "En curso", pausado: "En pausa", completo: "Completado" }[rep.estado];
  el.resEstado.textContent = texto ? `${texto}: ${visitados} de ${total} nodos visitados` : "Sin iniciar";
}

// Estado general que aparece en la barra superior.
function actualizarEstadoGlobal() {
  let texto = "Árbol listo para animar";
  let tono = "neutro";
  if (modelo.hayError) [texto, tono] = ["Entrada no válida", "error"];
  else if (!modelo.arbol) [texto, tono] = ["Esperando datos", "neutro"];
  else if (inorden.estado === "reproduciendo") [texto, tono] = ["Recorrido Inorden en curso", "activo"];
  else if (inorden.estado === "pausado") [texto, tono] = ["Recorrido en pausa", "aviso"];
  else if (inorden.estado === "completo") [texto, tono] = ["Recorrido completado", "ok"];
  else if (insercion.estado === "reproduciendo") [texto, tono] = ["Construyendo el árbol", "activo"];
  else if (insercion.estado === "pausado") [texto, tono] = ["Inserción en pausa", "aviso"];
  else if (insercion.estado === "completo") [texto, tono] = ["Árbol construido", "ok"];
  el.estadoTexto.textContent = texto;
  el.chipEstado.dataset.tono = tono;
}

const BLOQUEADO = "Espera la inserción";

const insercion = new Reproductor({
  retardo: () => Number($("ins-vel").value),
  alMostrar: mostrarInsercion,
  alCambiar: (rep) => {
    actualizarPanel("ins", rep, true);
    if (rep.estado === "completo") alCompletarInsercion();
    else if (inorden.indice >= 0) inorden.reiniciar();          // el recorrido ya no corresponde al árbol mostrado
    actualizarPanel("ino", inorden, rep.estado === "completo", BLOQUEADO);
    actualizarEstadoGlobal();
  },
});

const inorden = new Reproductor({
  retardo: () => Number($("ino-vel").value),
  alMostrar: mostrarInorden,
  alCambiar: (rep) => {
    actualizarPanel("ino", rep, insercion.estado === "completo", BLOQUEADO);
    actualizarEstadoRecorrido(rep);
    actualizarEstadoGlobal();
  },
});

function enlazarControles(prefijo, rep) {
  const enlazar = (nombre, accion) => $(`${prefijo}-${nombre}`).addEventListener("click", accion);
  enlazar("reproducir", () => rep.reproducir());
  enlazar("pausar", () => rep.pausar());
  enlazar("continuar", () => rep.continuar());
  enlazar("reiniciar", () => rep.reiniciar());
  enlazar("anterior", () => rep.anterior());
  enlazar("siguiente", () => rep.siguiente());
  enlazar("completo", () => rep.mostrarTodo());
}

/* ==========================================================================
   5) COMUNICACIÓN CON PYTHON (Flask)
   ========================================================================== */

// [AYUDA: comunicacion]
async function pedirJSON(url, opciones = {}) {
  const respuesta = await fetch(url, opciones);
  return respuesta.json();                  // Flask siempre responde con JSON
}

async function construirArbol() {
  const datos = await pedirJSON("/api/construir", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ texto: el.entrada.value }),
  });
  if (!datos.ok) {
    mostrarErrores(datos.errores);          // Python rechazó la entrada: no hay árbol nuevo
    return;
  }
  cargarArbolNuevo(datos);                  // Python construyó el árbol: lo dibujamos y lo animamos
}
// [/AYUDA]

function cargarArbolNuevo(datos) {
  modelo.version++;
  insercion.cargar(0);                      // detiene cualquier animación anterior
  inorden.cargar(0);
  modelo.arbol = datos.arbol;
  modelo.pasosInsercion = datos.pasos_insercion;
  modelo.pasosInorden = [];
  modelo.resultado = [];
  modelo.aparicion = new Map();
  datos.pasos_insercion.forEach((paso, i) => {
    if (paso.tipo === "raiz" || paso.tipo === "insertar") modelo.aparicion.set(paso.valor, i);
  });
  modelo.dibujo = dibujarArbol(el.svg, datos.arbol.nodos);
  el.svg.classList.remove("oculto");
  el.vacio.hidden = true;
  ajustarEscala();
  cerrarAlerta();
  ponerPista(datos.avisos);
  insercion.cargar(datos.pasos_insercion.length);
  insercion.reproducir();                   // la inserción se anima sola al construir
}

async function alCompletarInsercion() {
  if (modelo.inordenPedido === modelo.version) return;   // los pasos de este árbol ya se pidieron
  modelo.inordenPedido = modelo.version;
  const version = modelo.version;
  try {
    const datos = await pedirJSON("/api/inorden");
    if (version !== modelo.version) return;              // llegó tarde: ya hay otro árbol
    if (!datos.ok) { ponerMensaje(datos.errores[0]); return; }
    modelo.pasosInorden = datos.pasos;
    modelo.resultado = datos.resultado;
    inorden.cargar(datos.pasos.length);
  } catch (error) {
    modelo.inordenPedido = -1;
    ponerMensaje("No se pudieron pedir los pasos del recorrido al servidor.");
  }
}

async function alPulsarConstruir() {
  el.btnConstruir.disabled = true;
  try {
    await construirArbol();
  } catch (error) {
    console.error(error);
    mostrarErrores([error instanceof TypeError
      ? "No hay comunicación con el servidor Flask. ¿Sigue ejecutándose «python app.py»?"
      : "Ocurrió un error inesperado en la interfaz (más detalles en la consola del navegador)."]);
  } finally {
    el.btnConstruir.disabled = false;
  }
}

function mostrarErrores(errores) {
  el.alertaLista.replaceChildren(...errores.map((texto) => {
    const li = document.createElement("li");
    li.textContent = texto;
    return li;
  }));
  el.alerta.hidden = false;
  el.entrada.setAttribute("aria-invalid", "true");
  modelo.hayError = true;
  actualizarEstadoGlobal();
}

function cerrarAlerta() {
  el.alerta.hidden = true;
  el.entrada.removeAttribute("aria-invalid");
  modelo.hayError = false;
  actualizarEstadoGlobal();
}

async function limpiar() {
  modelo.version++;
  insercion.cargar(0);
  inorden.cargar(0);
  modelo.arbol = null;
  modelo.dibujo = null;
  modelo.pasosInsercion = [];
  modelo.pasosInorden = [];
  modelo.resultado = [];
  modelo.aparicion = new Map();
  el.svg.replaceChildren();
  el.svg.classList.add("oculto");
  el.vacio.hidden = false;
  el.entrada.value = "";
  ponerPista([]);
  ponerAviso([]);
  ponerMetricas([], false);
  el.resInorden.textContent = "—";
  el.resComparacion.textContent = "—";
  ponerMensaje("Escribe los números y pulsa «Construir árbol».");
  cerrarAlerta();
  actualizarEstadoRecorrido(inorden);
  el.entrada.focus();
  try {
    await pedirJSON("/api/reiniciar", { method: "POST" });   // Python olvida el árbol anterior
  } catch (error) {
    console.error(error);
  }
}

/* ==========================================================================
   6) NAVEGACIÓN Y SECCIONES DE AYUDA
   ========================================================================== */

function mostrarVista(nombre) {
  document.querySelectorAll(".vista").forEach((vista) => { vista.hidden = vista.id !== `vista-${nombre}`; });
  document.querySelectorAll(".menu-item").forEach((boton) => {
    const activo = boton.dataset.vista === nombre;
    boton.classList.toggle("activo", activo);
    boton.setAttribute("aria-current", activo ? "page" : "false");
  });
  if (nombre !== "arbol") {                   // al salir de la pantalla de trabajo las animaciones se pausan
    insercion.pausar();
    inorden.pausar();
  } else {
    ajustarEscala();
  }
}

function mostrarBloque(nombre) {
  document.querySelectorAll(".bloque").forEach((bloque) => { bloque.hidden = bloque.id !== `bloque-${nombre}`; });
  document.querySelectorAll(".ayuda-item").forEach((boton) => {
    const activo = boton.dataset.bloque === nombre;
    boton.classList.toggle("activo", activo);
    boton.setAttribute("aria-current", activo ? "true" : "false");
  });
  document.querySelector(".ayuda-contenido").scrollTop = 0;
}

// Dibuja los árboles pequeños de «¿Qué es un ABB?» con el mismo código de dibujo (datos reales de Python).
function dibujarEjemplos() {
  const datos = JSON.parse($("datos-ejemplos").textContent);

  const principal = dibujarArbol($("svg-ej-principal"), datos.principal);
  mostrarTodo(principal);
  for (const valor of [50, 30]) principal.vista.get(valor).visual.classList.add("camino");   // camino para insertar el 40
  principal.vista.get(30).arista.classList.add("camino");
  principal.vista.get(40).visual.classList.add("nuevo");
  principal.vista.get(40).arista.classList.add("nueva");

  mostrarTodo(dibujarArbol($("svg-ej-degenerado"), datos.degenerado));
}

/* ==========================================================================
   7) ARRANQUE
   ========================================================================== */

function iniciar() {
  el.btnConstruir.addEventListener("click", alPulsarConstruir);
  el.btnLimpiar.addEventListener("click", limpiar);
  el.alertaCerrar.addEventListener("click", cerrarAlerta);
  el.entrada.addEventListener("input", () => { if (modelo.hayError) cerrarAlerta(); });

  enlazarControles("ins", insercion);
  enlazarControles("ino", inorden);

  document.querySelectorAll(".menu-item").forEach((boton) => {
    boton.addEventListener("click", () => mostrarVista(boton.dataset.vista));
  });
  document.querySelectorAll(".ayuda-item").forEach((boton) => {
    boton.addEventListener("click", () => mostrarBloque(boton.dataset.bloque));
  });

  new ResizeObserver(ajustarEscala).observe(el.lienzo);
  dibujarEjemplos();
  limpiar();                                  // estado inicial: pantalla vacía y servidor sin árbol
}

iniciar();
