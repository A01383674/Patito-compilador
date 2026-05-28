"""
semantica.py  –  Análisis semántico y generación de cuádruplos para Patito.

Fase 4:
  · Cada variable recibe una dirección virtual al declararse (Fase 1).
  · Los cuádruplos condicionales (si/sino) usan GOTOF + GOTO con backpatching.
  · Los cuádruplos cíclicos (mientras) usan GOTOF + GOTO con backpatching.
  · Las funciones generan FUNC / ENDFUNC en su declaración y
    ERA / PARAM / GOSUB en su invocación.
  · El programa principal comienza con GOTO (para saltar las funciones)
    y termina con END.
"""

from lark import Tree, Token
from memoria   import MemoriaVirtual
from cuadruplos import GeneradorCuadruplos


class ErrorSemantico(Exception):
    pass


# ── TABLA DE VARIABLES ─────────────────────────────────────────────────────────

class TablaVariables:
    def __init__(self, nombre_scope: str):
        self.scope  = nombre_scope
        self._tabla = {}

    def agregar(self, nombre: str, tipo: str, direccion: int = None):
        if nombre in self._tabla:
            raise ErrorSemantico(
                f"Variable '{nombre}' ya declarada en scope '{self.scope}'"
            )
        self._tabla[nombre] = {'tipo': tipo, 'dir': direccion}

    def buscar(self, nombre: str):
        return self._tabla.get(nombre)

    def existe(self, nombre: str) -> bool:
        return nombre in self._tabla

    def items(self):
        return self._tabla.items()

    def imprimir(self):
        if not self._tabla:
            print("    (vacía)")
            return
        print(f"    {'VARIABLE':<20} {'TIPO':<12} DIR")
        print(f"    {'-'*40}")
        for nombre, info in self._tabla.items():
            dir_ = str(info.get('dir', '?'))
            print(f"    {nombre:<20} {info['tipo']:<12} {dir_}")

    def __len__(self):
        return len(self._tabla)

    def __repr__(self):
        return f"TablaVariables(scope='{self.scope}', vars={list(self._tabla.keys())})"


# ── ENTRADA DE FUNCIÓN ─────────────────────────────────────────────────────────

class EntradaFuncion:
    def __init__(self, nombre: str, tipo_retorno: str):
        self.nombre       = nombre
        self.tipo_retorno = tipo_retorno
        self.params       = []
        self.tabla_vars   = TablaVariables(nombre)
        self.quad_inicio  = None    # índice del cuádruplo FUNC (se llena en Fase 2)

    def __repr__(self):
        return (f"EntradaFuncion(nombre='{self.nombre}', "
                f"retorno='{self.tipo_retorno}', params={self.params})")


# ── DIRECTORIO DE FUNCIONES ────────────────────────────────────────────────────

class DirectorioFunciones:
    def __init__(self):
        self._directorio = {}

    def agregar_funcion(self, nombre: str, tipo_retorno: str) -> EntradaFuncion:
        if nombre in self._directorio:
            raise ErrorSemantico(f"Función '{nombre}' ya declarada")
        entrada = EntradaFuncion(nombre, tipo_retorno)
        self._directorio[nombre] = entrada
        return entrada

    def agregar_param(self, nombre_func: str, nombre_param: str,
                      tipo: str, direccion: int = None):
        entrada = self._directorio[nombre_func]
        entrada.params.append({'nombre': nombre_param, 'tipo': tipo, 'dir': direccion})
        entrada.tabla_vars.agregar(nombre_param, tipo, direccion)

    def buscar(self, nombre: str):
        return self._directorio.get(nombre)

    def existe(self, nombre: str) -> bool:
        return nombre in self._directorio

    def imprimir(self):
        if not self._directorio:
            print("  (sin funciones declaradas)")
            return
        for nombre, entrada in self._directorio.items():
            params_str = ", ".join(
                f"{p['nombre']}:{p['tipo']}@{p['dir']}" for p in entrada.params
            ) or "sin parámetros"
            quad_str = str(entrada.quad_inicio) if entrada.quad_inicio is not None else '?'
            print(f"\n  ┌─ Función   : {nombre}")
            print(f"  │  Retorno   : {entrada.tipo_retorno}")
            print(f"  │  Params    : {params_str}")
            print(f"  │  Quad FUNC : {quad_str}")
            print(f"  │  Variables locales:")
            entrada.tabla_vars.imprimir()

    def __len__(self):
        return len(self._directorio)

    def __repr__(self):
        return f"DirectorioFunciones(funciones={list(self._directorio.keys())})"


# ── HELPERS ────────────────────────────────────────────────────────────────────

def _trees(nodo, data):
    return [c for c in nodo.children if isinstance(c, Tree) and c.data == data]

def _tokens(nodo, tipo):
    return [c for c in nodo.children if isinstance(c, Token) and c.type == tipo]

def _first_tree(nodo, data):
    r = _trees(nodo, data)
    return r[0] if r else None

def _first_token(nodo, tipo):
    r = _tokens(nodo, tipo)
    return r[0] if r else None

def _resolver_tipo_retorno(retorno_node) -> str:
    """
    Extrae el tipo de retorno de un nodo 'retorno'.
    retorno : NULA | tipo
    tipo    : ENTERO | FLOTANTE
    """
    child = retorno_node.children[0]
    if isinstance(child, Token):          # Token NULA → "nula"
        return str(child)
    else:                                 # Tree('tipo', [Token(ENTERO/FLOTANTE)])
        return str(child.children[0])


# ── ANALIZADOR SEMÁNTICO ───────────────────────────────────────────────────────

class AnalizadorSemantico:

    def __init__(self):
        self.memoria       = MemoriaVirtual()
        self.dir_funciones = DirectorioFunciones()
        self.tabla_global  = TablaVariables('global')
        self.scope_actual  = None
        self.errores       = []
        self.generador     = None

    def analizar(self, arbol: Tree) -> bool:
        # ── Fase 1: poblar tablas y asignar direcciones ───────────────────────
        self._visitar(arbol)

        # ── Inicializar generador con tablas y memoria ya llenadas ────────────
        self.generador = GeneradorCuadruplos(
            self.tabla_global, self.dir_funciones, self.memoria
        )

        # ── Fase 2: generar cuádruplos ────────────────────────────────────────
        self.scope_actual = None
        self._generar(arbol)

        # Recoger errores del generador
        self.errores.extend(self.generador.errores)

        if self.errores:
            print(f"\n✗ Análisis semántico: {len(self.errores)} error(es):")
            for i, err in enumerate(self.errores, 1):
                print(f"  [{i}] {err}")
            return False

        print("\n✓ Análisis semántico y generación de cuádruplos exitosos")
        return True

    # ── Fase 1: llenar tablas de variables y directorio de funciones ──────────

    def _visitar(self, nodo):
        if isinstance(nodo, Tree):
            getattr(self, f'_v_{nodo.data}', self._v_default)(nodo)

    def _v_default(self, nodo):
        for hijo in nodo.children:
            self._visitar(hijo)

    def _v_programa(self, nodo):
        self.scope_actual = None
        for hijo in nodo.children:
            self._visitar(hijo)

    def _v_var_decl(self, nodo):
        """Declara variables asignándoles dirección virtual."""
        idlist_node = _first_tree(nodo, 'idlist')
        tipo_node   = _first_tree(nodo, 'tipo')
        tipo        = str(tipo_node.children[0])        # "entero" | "flotante"

        for token_id in _tokens(idlist_node, 'ID'):
            nombre = str(token_id)
            try:
                if self.scope_actual is None:
                    dir_ = self.memoria.asignar('global', tipo)
                    self.tabla_global.agregar(nombre, tipo, dir_)
                else:
                    dir_ = self.memoria.asignar('local', tipo)
                    self.dir_funciones.buscar(self.scope_actual) \
                        .tabla_vars.agregar(nombre, tipo, dir_)
            except ErrorSemantico as e:
                self.errores.append(str(e))

    def _v_func_decl(self, nodo):
        """Registra la función y asigna direcciones a parámetros/variables locales."""
        retorno_node = _first_tree(nodo, 'retorno')
        nombre_func  = str(_first_token(nodo, 'ID'))
        tipo_retorno = _resolver_tipo_retorno(retorno_node)

        try:
            self.dir_funciones.agregar_funcion(nombre_func, tipo_retorno)
        except ErrorSemantico as e:
            self.errores.append(str(e))
            return

        scope_previo      = self.scope_actual
        self.scope_actual = nombre_func

        # Reiniciar el segmento local para que cada función arranque en 3000
        self.memoria.reiniciar_local()

        params_node = _first_tree(nodo, 'params')
        vars_node   = _first_tree(nodo, 'vars')

        if params_node:
            self._v_params(params_node, nombre_func)
        if vars_node:
            self._visitar(vars_node)

        self.scope_actual = scope_previo

    def _v_params(self, nodo, nombre_func: str):
        """Declara los parámetros formales con sus direcciones locales."""
        ids   = _tokens(nodo, 'ID')
        tipos = _trees(nodo, 'tipo')
        for token_id, tipo_node in zip(ids, tipos):
            tipo = str(tipo_node.children[0])
            dir_ = self.memoria.asignar('local', tipo)
            try:
                self.dir_funciones.agregar_param(
                    nombre_func, str(token_id), tipo, dir_
                )
            except ErrorSemantico as e:
                self.errores.append(str(e))

    def _buscar_variable(self, nombre: str):
        if self.scope_actual:
            entrada = self.dir_funciones.buscar(self.scope_actual)
            if entrada:
                r = entrada.tabla_vars.buscar(nombre)
                if r:
                    return r
        return self.tabla_global.buscar(nombre)

    # ── Fase 2: generar cuádruplos ─────────────────────────────────────────────

    def _generar(self, nodo):
        if isinstance(nodo, Tree):
            getattr(self, f'_g_{nodo.data}', self._g_default)(nodo)

    def _g_default(self, nodo):
        for hijo in nodo.children:
            self._generar(hijo)

    def _g_programa(self, nodo):
        """
        Estructura del programa principal:
          0:  GOTO  →  [inicio del cuerpo principal]    (salta definiciones)
          …   FUNC / cuerpo / ENDFUNC  por cada función
          N:  [cuerpo principal]
          M:  END
        """
        self.scope_actual = None
        self.generador.scope_actual = None

        # GOTO para saltar las definiciones de funciones
        goto_main = self.generador.emitir_goto()

        # Generar código de cada función declarada
        funcs_node = _first_tree(nodo, 'funcs')
        if funcs_node:
            self._generar(funcs_node)

        # El cuerpo principal empieza aquí
        self.generador.rellenar(goto_main, self.generador.contador_quads())

        # Generar cuerpo principal
        cuerpo_node = _first_tree(nodo, 'cuerpo')
        if cuerpo_node:
            self._generar(cuerpo_node)

        # Cuádruplo de fin
        self.generador.emitir_end()

    def _g_func_decl(self, nodo):
        """
        Declaración de función:
          FUNC  nombre
          … cuerpo de la función …
          ENDFUNC
        Registra el índice de FUNC en el directorio.
        """
        nombre_func = str(_first_token(nodo, 'ID'))

        # Activar scope local
        self.scope_actual           = nombre_func
        self.generador.scope_actual = nombre_func

        # Cuádruplo FUNC  (guardamos su índice en el directorio)
        quad_func = self.generador.procesar_func_inicio(nombre_func)
        entrada   = self.dir_funciones.buscar(nombre_func)
        if entrada:
            entrada.quad_inicio = quad_func

        # Generar cuerpo
        cuerpo = _first_tree(nodo, 'cuerpo')
        if cuerpo:
            self._generar(cuerpo)

        # Cuádruplo ENDFUNC
        self.generador.procesar_func_fin()

        # Restaurar scope global
        self.scope_actual           = None
        self.generador.scope_actual = None

    # ── Estatutos ─────────────────────────────────────────────────────────────

    def _g_asigna(self, nodo):
        """Verifica declaración y genera cuádruplos de asignación."""
        id_token = _first_token(nodo, 'ID')
        if id_token and not self._buscar_variable(str(id_token)):
            self.errores.append(
                f"Variable '{id_token}' usada sin declarar "
                f"en scope '{self.scope_actual or 'global'}'"
            )
        self.generador.procesar_asigna(nodo)

    def _g_condicion(self, nodo):
        """
        si (expresion) { cuerpo } [sino { cuerpo }]

        Cuádruplos generados:
          [expr]
          GOTOF  cond  _  ?        ← destino pendiente
          [cuerpo verdadero]
          GOTO   _     _  ?        ← solo si hay sino; destino pendiente
          [cuerpo falso]           ← rellena GOTOF aquí si hay sino
          [siguiente]              ← rellena GOTO (y GOTOF si no hay sino) aquí
        """
        exp_node = _first_tree(nodo, 'expresion')
        cuerpos  = _trees(nodo, 'cuerpo')

        # Evaluar condición
        self.generador.evaluar_expresion(exp_node)
        cond_addr, _ = self.generador.pop_resultado()

        # GOTOF con destino pendiente
        gotof_idx = self.generador.emitir_gotof(cond_addr)

        # Cuerpo del SI (verdadero)
        self._generar(cuerpos[0])

        if len(cuerpos) == 2:
            # Con SINO: emitir GOTO para saltar el bloque SINO
            goto_idx = self.generador.emitir_goto()
            # Rellenar GOTOF → inicio del SINO
            self.generador.rellenar(gotof_idx, self.generador.contador_quads())
            # Cuerpo del SINO (falso)
            self._generar(cuerpos[1])
            # Rellenar GOTO → después del SINO
            self.generador.rellenar(goto_idx, self.generador.contador_quads())
        else:
            # Sin SINO: rellenar GOTOF → después del SI
            self.generador.rellenar(gotof_idx, self.generador.contador_quads())

    def _g_ciclo(self, nodo):
        """
        mientras (expresion) haz { cuerpo } ;

        Cuádruplos generados:
          [inicio_cond]
          [expr]
          GOTOF  cond  _  ?        ← destino pendiente (salida del ciclo)
          [cuerpo]
          GOTO   _     _  inicio_cond
          [siguiente]              ← rellena GOTOF aquí
        """
        exp_node = _first_tree(nodo, 'expresion')
        cuerpo   = _first_tree(nodo, 'cuerpo')

        # Guardar posición de inicio de la condición
        inicio_cond = self.generador.contador_quads()

        # Evaluar condición
        self.generador.evaluar_expresion(exp_node)
        cond_addr, _ = self.generador.pop_resultado()

        # GOTOF con destino pendiente (salida del ciclo)
        gotof_idx = self.generador.emitir_gotof(cond_addr)

        # Generar cuerpo del ciclo
        if cuerpo:
            self._generar(cuerpo)

        # GOTO de regreso al inicio de la condición
        self.generador.emitir_goto_a(inicio_cond)

        # Rellenar GOTOF → después del ciclo
        self.generador.rellenar(gotof_idx, self.generador.contador_quads())

    def _g_imprime(self, nodo):
        """Genera cuádruplos PRINT."""
        self.generador.procesar_imprime(nodo)

    def _g_llamada(self, nodo):
        """
        Genera ERA + PARAMs + GOSUB verificando existencia y aridad.
        """
        id_token = _first_token(nodo, 'ID')
        nombre   = str(id_token)

        if not self.dir_funciones.existe(nombre):
            self.errores.append(f"Función '{nombre}' no declarada")
            return

        entrada   = self.dir_funciones.buscar(nombre)
        args_node = _first_tree(nodo, 'args')
        n_args    = len(_trees(args_node, 'expresion')) if args_node else 0
        n_params  = len(entrada.params)

        if n_args != n_params:
            self.errores.append(
                f"Función '{nombre}' espera {n_params} argumento(s), "
                f"se pasaron {n_args}"
            )
            return

        self.generador.procesar_llamada(nodo)

    # ── Impresión ──────────────────────────────────────────────────────────────

    def imprimir_estructuras(self):
        print("\n" + "═" * 55)
        print("  TABLA DE VARIABLES GLOBALES")
        print("═" * 55)
        self.tabla_global.imprimir()

        print("\n" + "═" * 55)
        print("  DIRECTORIO DE FUNCIONES")
        print("═" * 55)
        self.dir_funciones.imprimir()

    def imprimir_memoria(self):
        print("\n" + "═" * 55)
        print("  MAPA DE MEMORIA VIRTUAL")
        print("═" * 55)
        self.memoria.imprimir()

    def imprimir_cuadruplos(self):
        print("\n" + "═" * 55)
        print("  CUÁDRUPLOS GENERADOS")
        print("═" * 55)
        if self.generador:
            self.generador.fila.imprimir()
        print()

    def imprimir_todo(self):
        self.imprimir_estructuras()
        self.imprimir_memoria()
        self.imprimir_cuadruplos()