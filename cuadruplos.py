from lark import Tree, Token


#  CUBO SEMÁNTICO


CUBO = {
    'entero': {
        'entero':   {'+':'entero', '-':'entero', '*':'entero', '/':'entero',
                     '>':'entero', '<':'entero', '==':'entero', '!=':'entero'},
        'flotante': {'+':'flotante','-':'flotante','*':'flotante','/':'flotante',
                     '>':'entero', '<':'entero', '==':'entero', '!=':'entero'},
    },
    'flotante': {
        'entero':   {'+':'flotante','-':'flotante','*':'flotante','/':'flotante',
                     '>':'entero', '<':'entero', '==':'entero', '!=':'entero'},
        'flotante': {'+':'flotante','-':'flotante','*':'flotante','/':'flotante',
                     '>':'entero', '<':'entero', '==':'entero', '!=':'entero'},
    },
}

TOKEN_A_OP = {
    'MAS':'+', 'MENOS':'-', 'MULT':'*', 'DIV':'/',
    'MAYOR_QUE':'>', 'MENOR_QUE':'<', 'IGUAL_IGUAL':'==', 'DIFERENTE':'!='
}

#  CUÁDRUPLO

class Cuadruplo:
    """
    Unidad de código intermedio: (operador, operando1, operando2, resultado)
    operando2 = None cuando la operación es unaria o de asignación simple.
    """
    def __init__(self, operador, operando1, operando2, resultado):
        self.operador  = operador
        self.operando1 = operando1
        self.operando2 = operando2
        self.resultado = resultado

    def __repr__(self):
        op2 = self.operando2 if self.operando2 is not None else '_'
        return f"({self.operador}, {self.operando1}, {op2}, {self.resultado})"

#  PILA DE OPERANDOS
#  Almacena nombres de variables, constantes literales y temporales (t1, t2…)
class PilaOperandos:
    def __init__(self):
        self._pila = []

    def push(self, operando: str):
        self._pila.append(operando)

    def pop(self) -> str:
        if self.vacia():
            raise IndexError("PilaOperandos vacía")
        return self._pila.pop()

    def top(self):
        return self._pila[-1] if self._pila else None

    def vacia(self) -> bool:
        return len(self._pila) == 0

    def __repr__(self):
        return f"PilaOperandos({self._pila})"

#  PILA DE OPERADORES
#  Almacena operadores aritméticos y relacionales

class PilaOperadores:
    def __init__(self):
        self._pila = []

    def push(self, operador: str):
        self._pila.append(operador)

    def pop(self) -> str:
        if self.vacia():
            raise IndexError("PilaOperadores vacía")
        return self._pila.pop()

    def top(self):
        return self._pila[-1] if self._pila else None

    def vacia(self) -> bool:
        return len(self._pila) == 0

    def __repr__(self):
        return f"PilaOperadores({self._pila})"

#  PILA DE TIPOS
#  Almacena el tipo ('entero' o 'flotante') de cada operando en la pila

class PilaTipos:
    def __init__(self):
        self._pila = []

    def push(self, tipo: str):
        self._pila.append(tipo)

    def pop(self) -> str:
        if self.vacia():
            raise IndexError("PilaTipos vacía")
        return self._pila.pop()

    def top(self):
        return self._pila[-1] if self._pila else None

    def vacia(self) -> bool:
        return len(self._pila) == 0

    def __repr__(self):
        return f"PilaTipos({self._pila})"


#  FILA DE CUÁDRUPLOS
#  Cola que acumula los cuádruplos en orden de generación

class FilaCuadruplos:
    def __init__(self):
        self._fila   = []
        self._indice = 0

    def encolar(self, cuad: Cuadruplo) -> int:
        """Agrega un cuádruplo al final y retorna su número de índice."""
        num = self._indice
        self._fila.append(cuad)
        self._indice += 1
        return num

    def ver(self, indice: int) -> Cuadruplo:
        return self._fila[indice]

    def tamanio(self) -> int:
        return len(self._fila)

    def vacia(self) -> bool:
        return len(self._fila) == 0

    def imprimir(self):
        if self.vacia():
            print("    (sin cuádruplos)")
            return
        print(f"  {'#':<5} {'OPERADOR':<10} {'OP1':<15} {'OP2':<15} RESULTADO")
        print(f"  {'-'*58}")
        for i, c in enumerate(self._fila):
            op2 = str(c.operando2) if c.operando2 is not None else '_'
            print(f"  {i:<5} {str(c.operador):<10} {str(c.operando1):<15} {op2:<15} {str(c.resultado)}")

    def __iter__(self):
        return iter(self._fila)

    def __repr__(self):
        return f"FilaCuadruplos({self._fila})"


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

def _op_token(nodo):
    """Retorna el primer token que sea operador aritmético o relacional."""
    for c in nodo.children:
        if isinstance(c, Token) and c.type in TOKEN_A_OP:
            return c
    return None


#  GENERADOR DE CUÁDRUPLOS
#  Usa las tres pilas y la fila para traducir expresiones y estatutos

class GeneradorCuadruplos:
    def __init__(self, tabla_global, dir_funciones):
        self.tabla_global    = tabla_global
        self.dir_funciones   = dir_funciones

        # Las tres pilas
        self.p_operandos     = PilaOperandos()
        self.p_operadores    = PilaOperadores()
        self.p_tipos         = PilaTipos()

        # La fila de cuádruplos
        self.fila            = FilaCuadruplos()

        # Contador de variables temporales
        self._cont_temp      = 0

        # Scope activo (para resolución de tipos)
        self.scope_actual    = None

        # Errores de tipo detectados durante generación
        self.errores         = []

    #  utilidades 

    def _nuevo_temp(self) -> str:
        self._cont_temp += 1
        return f"t{self._cont_temp}"

    def _buscar_tipo(self, nombre: str) -> str:
        if self.scope_actual:
            entrada = self.dir_funciones.buscar(self.scope_actual)
            if entrada:
                info = entrada.tabla_vars.buscar(nombre)
                if info:
                    return info['tipo']
        info = self.tabla_global.buscar(nombre)
        return info['tipo'] if info else 'error'

    #  generación de un cuádruplo binario 

    def _generar_binario(self):
        op2    = self.p_operandos.pop()
        tipo2  = self.p_tipos.pop()
        op1    = self.p_operandos.pop()
        tipo1  = self.p_tipos.pop()
        oper   = self.p_operadores.pop()

        try:
            tipo_res = CUBO[tipo1][tipo2][oper]
        except KeyError:
            self.errores.append(f"Operación inválida: {tipo1} {oper} {tipo2}")
            tipo_res = 'error'

        temp = self._nuevo_temp()
        self.fila.encolar(Cuadruplo(oper, op1, op2, temp))
        self.p_operandos.push(temp)
        self.p_tipos.push(tipo_res)
        return temp, tipo_res

    #  puntos neurálgicos públicos (llamados desde AnalizadorSemantico) 

    def procesar_asigna(self, nodo: Tree):
        id_token = _first_token(nodo, 'ID')
        exp_node = _first_tree(nodo, 'expresion')
        if id_token and exp_node:
            self._visitar_expresion(exp_node)
            resultado = self.p_operandos.pop()
            self.p_tipos.pop()
            self.fila.encolar(Cuadruplo('=', resultado, None, str(id_token)))

    def procesar_condicion(self, nodo: Tree):
        exp_node = _first_tree(nodo, 'expresion')
        if exp_node:
            self._visitar_expresion(exp_node)
            resultado = self.p_operandos.pop()
            self.p_tipos.pop()
            return resultado
        return None

    def procesar_ciclo(self, nodo: Tree):
        exp_node = _first_tree(nodo, 'expresion')
        if exp_node:
            self._visitar_expresion(exp_node)
            resultado = self.p_operandos.pop()
            self.p_tipos.pop()
            return resultado
        return None

    def procesar_imprime(self, nodo: Tree):
        for hijo in nodo.children:
            if isinstance(hijo, Tree) and hijo.data == 'print_item':
                letrero_tok = _first_token(hijo, 'LETRERO')
                if letrero_tok:
                    self.fila.encolar(Cuadruplo('PRINT', str(letrero_tok), None, '_'))
                else:
                    exp_node = _first_tree(hijo, 'expresion')
                    if exp_node:
                        self._visitar_expresion(exp_node)
                        resultado = self.p_operandos.pop()
                        self.p_tipos.pop()
                        self.fila.encolar(Cuadruplo('PRINT', resultado, None, '_'))

    def procesar_llamada(self, nodo: Tree):
        id_token  = _first_token(nodo, 'ID')
        nombre    = str(id_token) if id_token else '?'
        args_node = _first_tree(nodo, 'args')

        if args_node:
            for exp_node in _trees(args_node, 'expresion'):
                self._visitar_expresion(exp_node)
                arg = self.p_operandos.pop()
                self.p_tipos.pop()
                self.fila.encolar(Cuadruplo('PARAM', arg, None, '_'))

        self.fila.encolar(Cuadruplo('CALL', nombre, None, '_'))

    #  visitores internos de expresión 

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

        # Signo unario
        if children and isinstance(children[0], Token) and children[0].type in ('MAS', 'MENOS'):
            sub = _first_tree(nodo, 'factor')
            if sub:
                self._visitar_factor(sub)
                if children[0].type == 'MENOS':
                    operando = self.p_operandos.pop()
                    tipo     = self.p_tipos.pop()
                    temp     = self._nuevo_temp()
                    self.fila.encolar(Cuadruplo('UMINUS', operando, None, temp))
                    self.p_operandos.push(temp)
                    self.p_tipos.push(tipo)
            return

        # Expresión entre paréntesis
        exp_node = _first_tree(nodo, 'expresion')
        if exp_node:
            self._visitar_expresion(exp_node)
            return

        # Llamada a función dentro de expresión
        llamada = _first_tree(nodo, 'llamada_expr')
        if llamada:
            id_token = _first_token(llamada, 'ID')
            nombre   = str(id_token)
            entrada  = self.dir_funciones.buscar(nombre)
            tipo_ret = entrada.tipo_retorno if entrada else 'error'
            args_node = _first_tree(llamada, 'args')
            if args_node:
                for exp in _trees(args_node, 'expresion'):
                    self._visitar_expresion(exp)
                    arg = self.p_operandos.pop()
                    self.p_tipos.pop()
                    self.fila.encolar(Cuadruplo('PARAM', arg, None, '_'))
            temp = self._nuevo_temp()
            self.fila.encolar(Cuadruplo('CALL', nombre, None, temp))
            self.p_operandos.push(temp)
            self.p_tipos.push(tipo_ret)
            return

        # Constante numérica
        cte_node = _first_tree(nodo, 'cte')
        if cte_node:
            token = cte_node.children[0]
            valor = str(token)
            tipo  = 'entero' if token.type == 'CTE_ENT' else 'flotante'
            self.p_operandos.push(valor)
            self.p_tipos.push(tipo)
            return

        # Identificador
        id_token = _first_token(nodo, 'ID')
        if id_token:
            nombre = str(id_token)
            tipo   = self._buscar_tipo(nombre)
            self.p_operandos.push(nombre)
            self.p_tipos.push(tipo)
            return