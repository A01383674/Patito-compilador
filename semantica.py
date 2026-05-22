from lark import Tree, Token
from cuadruplos import GeneradorCuadruplos


class ErrorSemantico(Exception):
    pass

#  TABLA DE VARIABLES

class TablaVariables:
    def __init__(self, nombre_scope: str):
        self.scope  = nombre_scope
        self._tabla = {}

    def agregar(self, nombre: str, tipo: str):
        if nombre in self._tabla:
            raise ErrorSemantico(
                f"Variable '{nombre}' ya fue declarada en el scope '{self.scope}'"
            )
        self._tabla[nombre] = {'tipo': tipo}

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
        print(f"    {'VARIABLE':<20} TIPO")
        print(f"    {'-'*30}")
        for nombre, info in self._tabla.items():
            print(f"    {nombre:<20} {info['tipo']}")

    def __len__(self):
        return len(self._tabla)

    def __repr__(self):
        return f"TablaVariables(scope='{self.scope}', vars={list(self._tabla.keys())})"

#  ENTRADA DE FUNCIÓN

class EntradaFuncion:
    def __init__(self, nombre: str, tipo_retorno: str):
        self.nombre       = nombre
        self.tipo_retorno = tipo_retorno
        self.params       = []
        self.tabla_vars   = TablaVariables(nombre)

    def __repr__(self):
        return (f"EntradaFuncion(nombre='{self.nombre}', "
                f"retorno='{self.tipo_retorno}', params={self.params})")

#  DIRECTORIO DE FUNCIONES

class DirectorioFunciones:
    def __init__(self):
        self._directorio = {}

    def agregar_funcion(self, nombre: str, tipo_retorno: str) -> EntradaFuncion:
        if nombre in self._directorio:
            raise ErrorSemantico(f"Función '{nombre}' ya fue declarada")
        entrada = EntradaFuncion(nombre, tipo_retorno)
        self._directorio[nombre] = entrada
        return entrada

    def agregar_param(self, nombre_func: str, nombre_param: str, tipo: str):
        entrada = self._directorio[nombre_func]
        entrada.params.append({'nombre': nombre_param, 'tipo': tipo})
        entrada.tabla_vars.agregar(nombre_param, tipo)

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
                f"{p['nombre']}:{p['tipo']}" for p in entrada.params
            ) or "sin parámetros"
            print(f"\n  ┌─ Función : {nombre}")
            print(f"  │  Retorno  : {entrada.tipo_retorno}")
            print(f"  │  Params   : {params_str}")
            print(f"  │  Variables locales:")
            entrada.tabla_vars.imprimir()

    def __len__(self):
        return len(self._directorio)

    def __repr__(self):
        return f"DirectorioFunciones(funciones={list(self._directorio.keys())})"

#  HELPERS

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

#  ANALIZADOR SEMÁNTICO

class AnalizadorSemantico:
    def __init__(self):
        self.dir_funciones = DirectorioFunciones()
        self.tabla_global  = TablaVariables('global')
        self.scope_actual  = None
        self.errores       = []
        self.generador     = None

    def analizar(self, arbol: Tree) -> bool:
        # ── Pasada 1: llenar directorio y tablas de variables ─────────────────
        self._visitar(arbol)

        # ── Inicializar generador con tablas ya llenadas ──────────────────────
        self.generador = GeneradorCuadruplos(self.tabla_global, self.dir_funciones)

        # ── Pasada 2: generar cuádruplos ──────────────────────────────────────
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

    #  Fase 1 — Llenar tablas de variables y directorio de funciones

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
        idlist_node = _first_tree(nodo, 'idlist')
        tipo_node   = _first_tree(nodo, 'tipo')
        tipo        = str(tipo_node.children[0])
        for token_id in _tokens(idlist_node, 'ID'):
            nombre = str(token_id)
            try:
                if self.scope_actual is None:
                    self.tabla_global.agregar(nombre, tipo)
                else:
                    self.dir_funciones.buscar(self.scope_actual).tabla_vars.agregar(nombre, tipo)
            except ErrorSemantico as e:
                self.errores.append(str(e))

    def _v_func_decl(self, nodo):
        retorno_node = _first_tree(nodo, 'retorno')
        nombre_func  = str(_first_token(nodo, 'ID'))
        tipo_retorno = str(retorno_node.children[0])
        try:
            self.dir_funciones.agregar_funcion(nombre_func, tipo_retorno)
        except ErrorSemantico as e:
            self.errores.append(str(e))
            return

        scope_previo      = self.scope_actual
        self.scope_actual = nombre_func
        params_node = _first_tree(nodo, 'params')
        vars_node   = _first_tree(nodo, 'vars')
        if params_node:
            self._v_params(params_node, nombre_func)
        if vars_node:
            self._visitar(vars_node)
        self.scope_actual = scope_previo

    def _v_params(self, nodo, nombre_func):
        ids   = _tokens(nodo, 'ID')
        tipos = _trees(nodo, 'tipo')
        for token_id, tipo_node in zip(ids, tipos):
            try:
                self.dir_funciones.agregar_param(
                    nombre_func, str(token_id), str(tipo_node.children[0]))
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

    #  Fase 2 — Generar cuádruplos

    def _generar(self, nodo):
        if isinstance(nodo, Tree):
            getattr(self, f'_g_{nodo.data}', self._g_default)(nodo)

    def _g_default(self, nodo):
        for hijo in nodo.children:
            self._generar(hijo)

    def _g_programa(self, nodo):
        self.scope_actual = None
        self.generador.scope_actual = None
        for hijo in nodo.children:
            self._generar(hijo)

    def _g_func_decl(self, nodo):
        """Activa el scope de la función, genera cuádruplos del cuerpo y lo restaura."""
        nombre_func = str(_first_token(nodo, 'ID'))
        self.scope_actual = nombre_func
        self.generador.scope_actual = nombre_func
        cuerpo = _first_tree(nodo, 'cuerpo')
        if cuerpo:
            self._generar(cuerpo)
        self.scope_actual = None
        self.generador.scope_actual = None

    def _g_asigna(self, nodo):
        """PN: id = expresion ; → verifica declaración y genera cuádruplos."""
        id_token = _first_token(nodo, 'ID')
        if id_token and not self._buscar_variable(str(id_token)):
            self.errores.append(
                f"Variable '{id_token}' usada sin declarar en scope '{self.scope_actual or 'global'}'"
            )
        self.generador.procesar_asigna(nodo)

    def _g_condicion(self, nodo):
        """PN: si (expresion) { cuerpo } [sino { cuerpo }]"""
        self.generador.procesar_condicion(nodo)
        for cuerpo in _trees(nodo, 'cuerpo'):
            self._generar(cuerpo)

    def _g_ciclo(self, nodo):
        """PN: mientras (expresion) haz { cuerpo } ;"""
        self.generador.procesar_ciclo(nodo)
        cuerpo = _first_tree(nodo, 'cuerpo')
        if cuerpo:
            self._generar(cuerpo)

    def _g_imprime(self, nodo):
        """PN: escribe(item, ...) → genera cuádruplos PRINT."""
        self.generador.procesar_imprime(nodo)

    def _g_llamada(self, nodo):
        """PN: id(args) ; → genera cuádruplos PARAM + CALL."""
        self.generador.procesar_llamada(nodo)

    # print

    def imprimir_estructuras(self):
        print("\n" + "═"*50)
        print("  TABLA DE VARIABLES GLOBALES")
        print("═"*50)
        self.tabla_global.imprimir()
        print("\n" + "═"*50)
        print("  DIRECTORIO DE FUNCIONES")
        print("═"*50)
        self.dir_funciones.imprimir()

    def imprimir_cuadruplos(self):
        print("\n" + "═"*50)
        print("  CUÁDRUPLOS GENERADOS")
        print("═"*50)
        if self.generador:
            self.generador.fila.imprimir()
        print()