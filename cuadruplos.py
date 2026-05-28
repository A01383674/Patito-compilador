"""
cuadruplos.py  –  Pilas, fila de cuádruplos y generador de código intermedio.

Fase 4 añade:
  · Direcciones virtuales (enteros) en lugar de nombres simbólicos.
  · API de backpatching: emitir_gotof / emitir_goto / emitir_goto_a / rellenar.
  · Cuádruplos para funciones: FUNC, ENDFUNC, ERA, PARAM, GOSUB.
  · Cuádruplos para flujo: GOTOF, GOTO, END.
"""

from lark import Tree, Token


# ── CUBO SEMÁNTICO ─────────────────────────────────────────────────────────────

CUBO = {
    'entero': {
        'entero':   {'+': 'entero',   '-': 'entero',   '*': 'entero',   '/': 'entero',
                     '>': 'entero',   '<': 'entero',   '==': 'entero',  '!=': 'entero'},
        'flotante': {'+': 'flotante', '-': 'flotante', '*': 'flotante', '/': 'flotante',
                     '>': 'entero',   '<': 'entero',   '==': 'entero',  '!=': 'entero'},
    },
    'flotante': {
        'entero':   {'+': 'flotante', '-': 'flotante', '*': 'flotante', '/': 'flotante',
                     '>': 'entero',   '<': 'entero',   '==': 'entero',  '!=': 'entero'},
        'flotante': {'+': 'flotante', '-': 'flotante', '*': 'flotante', '/': 'flotante',
                     '>': 'entero',   '<': 'entero',   '==': 'entero',  '!=': 'entero'},
    },
}

TOKEN_A_OP = {
    'MAS':        '+',  'MENOS':       '-',
    'MULT':       '*',  'DIV':         '/',
    'MAYOR_QUE':  '>',  'MENOR_QUE':   '<',
    'IGUAL_IGUAL':'==', 'DIFERENTE':   '!=',
}


# ── CUÁDRUPLO ──────────────────────────────────────────────────────────────────

class Cuadruplo:
    """
    Unidad de código intermedio: (operador, operando1, operando2, resultado).
    Los operandos de datos son direcciones virtuales (int).
    Los destinos de salto son índices de cuádruplo (int).
    Los nombres de función son cadenas.
    None/'_' indica campo no usado.
    """
    def __init__(self, operador, operando1, operando2, resultado):
        self.operador  = operador
        self.operando1 = operando1
        self.operando2 = operando2
        self.resultado = resultado

    def __repr__(self):
        op1 = '_' if self.operando1 is None else self.operando1
        op2 = '_' if self.operando2 is None else self.operando2
        res = '?' if self.resultado is None else self.resultado
        return f"({self.operador}, {op1}, {op2}, {res})"


# ── PILAS ──────────────────────────────────────────────────────────────────────

class PilaOperandos:
    def __init__(self):
        self._pila = []

    def push(self, operando):
        self._pila.append(operando)

    def pop(self):
        if not self._pila:
            raise IndexError("PilaOperandos vacía")
        return self._pila.pop()

    def top(self):
        return self._pila[-1] if self._pila else None

    def vacia(self):
        return not self._pila

    def __repr__(self):
        return f"PilaOperandos({self._pila})"


class PilaOperadores:
    def __init__(self):
        self._pila = []

    def push(self, op):
        self._pila.append(op)

    def pop(self):
        if not self._pila:
            raise IndexError("PilaOperadores vacía")
        return self._pila.pop()

    def top(self):
        return self._pila[-1] if self._pila else None

    def vacia(self):
        return not self._pila

    def __repr__(self):
        return f"PilaOperadores({self._pila})"


class PilaTipos:
    def __init__(self):
        self._pila = []

    def push(self, tipo):
        self._pila.append(tipo)

    def pop(self):
        if not self._pila:
            raise IndexError("PilaTipos vacía")
        return self._pila.pop()

    def top(self):
        return self._pila[-1] if self._pila else None

    def vacia(self):
        return not self._pila

    def __repr__(self):
        return f"PilaTipos({self._pila})"


# ── FILA DE CUÁDRUPLOS ─────────────────────────────────────────────────────────

class FilaCuadruplos:
    def __init__(self):
        self._fila   = []
        self._indice = 0

    def encolar(self, cuad: Cuadruplo) -> int:
        """Agrega el cuádruplo y retorna su número de índice."""
        num = self._indice
        self._fila.append(cuad)
        self._indice += 1
        return num

    def fill(self, indice: int, valor) -> None:
        """Backpatching: rellena el campo 'resultado' del cuádruplo en `indice`."""
        self._fila[indice].resultado = valor

    def ver(self, indice: int) -> Cuadruplo:
        return self._fila[indice]

    def tamanio(self) -> int:
        return len(self._fila)

    def vacia(self) -> bool:
        return not self._fila

    def imprimir(self):
        if self.vacia():
            print("    (sin cuádruplos)")
            return
        print(f"  {'#':<5} {'OPERADOR':<10} {'OP1':<15} {'OP2':<10} RESULTADO")
        print(f"  {'-'*58}")
        for i, c in enumerate(self._fila):
            op1 = '_' if c.operando1 is None else str(c.operando1)
            op2 = '_' if c.operando2 is None else str(c.operando2)
            res = '?' if c.resultado is None else str(c.resultado)
            print(f"  {i:<5} {str(c.operador):<10} {op1:<15} {op2:<10} {res}")

    def __iter__(self):
        return iter(self._fila)

    def __repr__(self):
        return f"FilaCuadruplos({self._fila})"


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

def _op_token(nodo):
    """Primer token que sea operador aritmético o relacional."""
    for c in nodo.children:
        if isinstance(c, Token) and c.type in TOKEN_A_OP:
            return c
    return None


# ── GENERADOR DE CUÁDRUPLOS ────────────────────────────────────────────────────

class GeneradorCuadruplos:
    """
    Genera cuádruplos con direcciones virtuales a partir del AST de Patito.

    Colabora con:
      · MemoriaVirtual  – para asignar/consultar direcciones.
      · TablaVariables  – via tabla_global y dir_funciones para resolver nombres.
      · AnalizadorSemantico – que llama los métodos públicos en los puntos neurálgicos.
    """

    def __init__(self, tabla_global, dir_funciones, memoria):
        self.tabla_global  = tabla_global
        self.dir_funciones = dir_funciones
        self.memoria       = memoria

        # Las tres pilas
        self.p_operandos  = PilaOperandos()
        self.p_operadores = PilaOperadores()
        self.p_tipos      = PilaTipos()

        # La fila de cuádruplos
        self.fila = FilaCuadruplos()

        # Scope en uso (para resolución de variables locales)
        self.scope_actual = None

        # Errores de tipo acumulados
        self.errores = []

    # ── Utilidades privadas ───────────────────────────────────────────────────

    def _nuevo_temp(self, tipo: str) -> int:
        """Asigna una nueva dirección temporal y la retorna."""
        seg_tipo = 'flotante' if tipo == 'flotante' else 'entero'
        return self.memoria.asignar('temp', seg_tipo)

    def _buscar_dir_tipo(self, nombre: str) -> tuple:
        """
        Busca `nombre` primero en el scope actual y luego en global.
        Retorna (dirección, tipo) o (None, 'error').
        """
        if self.scope_actual:
            entrada = self.dir_funciones.buscar(self.scope_actual)
            if entrada:
                info = entrada.tabla_vars.buscar(nombre)
                if info:
                    return info['dir'], info['tipo']
        info = self.tabla_global.buscar(nombre)
        if info:
            return info['dir'], info['tipo']
        return None, 'error'

    # ── Generación de cuádruplo binario ──────────────────────────────────────

    def _generar_binario(self):
        """Consume dos operandos y un operador; emite el cuádruplo correspondiente."""
        addr2, tipo2 = self.p_operandos.pop(), self.p_tipos.pop()
        addr1, tipo1 = self.p_operandos.pop(), self.p_tipos.pop()
        oper         = self.p_operadores.pop()

        try:
            tipo_res = CUBO[tipo1][tipo2][oper]
        except KeyError:
            self.errores.append(f"Operación inválida: {tipo1} {oper} {tipo2}")
            tipo_res = 'error'

        temp = self._nuevo_temp(tipo_res)
        self.fila.encolar(Cuadruplo(oper, addr1, addr2, temp))
        self.p_operandos.push(temp)
        self.p_tipos.push(tipo_res)
        return temp, tipo_res

    # ── API de backpatching (llamada desde AnalizadorSemantico) ───────────────

    def evaluar_expresion(self, nodo: Tree):
        """Genera cuádruplos para la expresión y deja el resultado en las pilas."""
        self._visitar_expresion(nodo)

    def pop_resultado(self) -> tuple:
        """Retira y retorna (dirección, tipo) del tope de las pilas de resultado."""
        return self.p_operandos.pop(), self.p_tipos.pop()

    def emitir_gotof(self, addr) -> int:
        """Emite  GOTOF  con destino pendiente (None). Retorna el índice."""
        return self.fila.encolar(Cuadruplo('GOTOF', addr, None, None))

    def emitir_goto(self) -> int:
        """Emite  GOTO  incondicionado con destino pendiente. Retorna el índice."""
        return self.fila.encolar(Cuadruplo('GOTO', None, None, None))

    def emitir_goto_a(self, destino: int) -> int:
        """Emite  GOTO  con destino ya conocido. Retorna el índice."""
        return self.fila.encolar(Cuadruplo('GOTO', None, None, destino))

    def rellenar(self, indice: int, destino: int):
        """Backpatching: rellena el campo resultado de un cuádruplo pendiente."""
        self.fila.fill(indice, destino)

    def contador_quads(self) -> int:
        """Retorna el número del próximo cuádruplo a emitir."""
        return self.fila.tamanio()

    def emitir_end(self):
        """Emite cuádruplo END (fin del programa)."""
        self.fila.encolar(Cuadruplo('END', None, None, None))

    # ── Puntos neurálgicos para estatutos ────────────────────────────────────

    def procesar_asigna(self, nodo: Tree):
        """PN asignación: genera cuádruplos de la expresión y emite '='."""
        id_token = _first_token(nodo, 'ID')
        exp_node = _first_tree(nodo, 'expresion')
        if not (id_token and exp_node):
            return
        self._visitar_expresion(exp_node)
        src_addr, _  = self.pop_resultado()
        dest_addr, _ = self._buscar_dir_tipo(str(id_token))
        if dest_addr is None:
            self.errores.append(
                f"Variable '{id_token}' no tiene dirección virtual (¿no declarada?)"
            )
            return
        self.fila.encolar(Cuadruplo('=', src_addr, None, dest_addr))

    def procesar_imprime(self, nodo: Tree):
        """PN escribe: emite PRINT por cada ítem (expresión o literal de cadena)."""
        for hijo in nodo.children:
            if not (isinstance(hijo, Tree) and hijo.data == 'print_item'):
                continue
            letrero_tok = _first_token(hijo, 'LETRERO')
            if letrero_tok:
                # Literal de cadena → dirección en pool de constantes
                valor = str(letrero_tok)
                dir_  = self.memoria.asignar_constante(valor, 'cadena')
                self.fila.encolar(Cuadruplo('PRINT', dir_, None, None))
            else:
                exp_node = _first_tree(hijo, 'expresion')
                if exp_node:
                    self._visitar_expresion(exp_node)
                    addr, _ = self.pop_resultado()
                    self.fila.encolar(Cuadruplo('PRINT', addr, None, None))

    def procesar_func_inicio(self, nombre_func: str):
        """Emite cuádruplo  FUNC  al entrar a una declaración de función."""
        self.fila.encolar(Cuadruplo('FUNC', nombre_func, None, None))

    def procesar_func_fin(self):
        """Emite cuádruplo  ENDFUNC  al cerrar una declaración de función."""
        self.fila.encolar(Cuadruplo('ENDFUNC', None, None, None))

    def procesar_llamada(self, nodo: Tree):
        """
        PN llamada (como estatuto):
          ERA  nombre
          PARAM  arg1  _  1
          PARAM  arg2  _  2  ...
          GOSUB  nombre  _  _
        """
        id_token  = _first_token(nodo, 'ID')
        nombre    = str(id_token) if id_token else '?'
        args_node = _first_tree(nodo, 'args')

        self.fila.encolar(Cuadruplo('ERA', nombre, None, None))

        param_num = 1
        if args_node:
            for exp_node in _trees(args_node, 'expresion'):
                self._visitar_expresion(exp_node)
                arg_addr, _ = self.pop_resultado()
                self.fila.encolar(Cuadruplo('PARAM', arg_addr, None, param_num))
                param_num += 1

        self.fila.encolar(Cuadruplo('GOSUB', nombre, None, None))

    # ── Visitores internos de expresión ──────────────────────────────────────

    def _visitar_expresion(self, nodo: Tree):
        hijos_exp = _trees(nodo, 'exp')
        op_rel    = _first_tree(nodo, 'op_rel')

        if op_rel and len(hijos_exp) == 2:
            self._visitar_exp(hijos_exp[0])
            op_str = TOKEN_A_OP[op_rel.children[0].type]
            self.p_operadores.push(op_str)
            self._visitar_exp(hijos_exp[1])
            self._generar_binario()
        elif hijos_exp:
            self._visitar_exp(hijos_exp[0])

    def _visitar_exp(self, nodo: Tree):
        hijos_exp  = _trees(nodo, 'exp')
        hijos_term = _trees(nodo, 'termino')
        op_token   = _op_token(nodo)

        if hijos_exp and op_token:
            self._visitar_exp(hijos_exp[0])
            self.p_operadores.push(TOKEN_A_OP[op_token.type])
            self._visitar_termino(hijos_term[0])
            self._generar_binario()
        elif hijos_term:
            self._visitar_termino(hijos_term[0])

    def _visitar_termino(self, nodo: Tree):
        hijos_term = _trees(nodo, 'termino')
        hijos_fac  = _trees(nodo, 'factor')
        op_token   = _op_token(nodo)

        if hijos_term and op_token:
            self._visitar_termino(hijos_term[0])
            self.p_operadores.push(TOKEN_A_OP[op_token.type])
            self._visitar_factor(hijos_fac[0])
            self._generar_binario()
        elif hijos_fac:
            self._visitar_factor(hijos_fac[0])

    def _visitar_factor(self, nodo: Tree):
        children = nodo.children

        # ── Signo unario ─────────────────────────────────────────────────────
        if children and isinstance(children[0], Token) and \
                children[0].type in ('MAS', 'MENOS'):
            sub = _first_tree(nodo, 'factor')
            if sub:
                self._visitar_factor(sub)
                if children[0].type == 'MENOS':
                    addr, tipo = self.pop_resultado()
                    temp = self._nuevo_temp(tipo)
                    self.fila.encolar(Cuadruplo('UMINUS', addr, None, temp))
                    self.p_operandos.push(temp)
                    self.p_tipos.push(tipo)
            return

        # ── Expresión entre paréntesis ────────────────────────────────────────
        exp_node = _first_tree(nodo, 'expresion')
        if exp_node:
            self._visitar_expresion(exp_node)
            return

        # ── Llamada a función en expresión (llamada_expr) ────────────────────
        llamada = _first_tree(nodo, 'llamada_expr')
        if llamada:
            id_token  = _first_token(llamada, 'ID')
            nombre    = str(id_token)
            entrada   = self.dir_funciones.buscar(nombre)

            if entrada is None:
                self.errores.append(f"Función '{nombre}' no declarada")
                self.p_operandos.push(-1)
                self.p_tipos.push('error')
                return

            tipo_ret = entrada.tipo_retorno
            if tipo_ret == 'nula':
                self.errores.append(
                    f"Función '{nombre}' es nula; no puede usarse en una expresión"
                )
                self.p_operandos.push(-1)
                self.p_tipos.push('error')
                return

            args_node = _first_tree(llamada, 'args')
            self.fila.encolar(Cuadruplo('ERA', nombre, None, None))
            param_num = 1
            if args_node:
                for exp in _trees(args_node, 'expresion'):
                    self._visitar_expresion(exp)
                    arg_addr, _ = self.pop_resultado()
                    self.fila.encolar(Cuadruplo('PARAM', arg_addr, None, param_num))
                    param_num += 1

            seg_tipo = 'flotante' if tipo_ret == 'flotante' else 'entero'
            temp = self.memoria.asignar('temp', seg_tipo)
            self.fila.encolar(Cuadruplo('GOSUB', nombre, None, temp))
            self.p_operandos.push(temp)
            self.p_tipos.push(tipo_ret)
            return

        # ── Constante numérica ────────────────────────────────────────────────
        cte_node = _first_tree(nodo, 'cte')
        if cte_node:
            token = cte_node.children[0]
            valor = str(token)
            tipo  = 'entero' if token.type == 'CTE_ENT' else 'flotante'
            dir_  = self.memoria.asignar_constante(valor, tipo)
            self.p_operandos.push(dir_)
            self.p_tipos.push(tipo)
            return

        # ── Identificador ─────────────────────────────────────────────────────
        id_token = _first_token(nodo, 'ID')
        if id_token:
            nombre = str(id_token)
            addr, tipo = self._buscar_dir_tipo(nombre)
            if addr is None:
                self.errores.append(
                    f"Variable '{nombre}' usada sin declarar "
                    f"en scope '{self.scope_actual or 'global'}'"
                )
                addr = -1
            self.p_operandos.push(addr)
            self.p_tipos.push(tipo)
            return