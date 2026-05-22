import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cuadruplos import PilaOperandos, PilaOperadores, PilaTipos, FilaCuadruplos, Cuadruplo
from patito_parser import crear_parser
from semantica import AnalizadorSemantico

parser = crear_parser()

def analizar(codigo):
    arbol = parser.parse(codigo)
    sem   = AnalizadorSemantico()
    sem.analizar(arbol)
    return sem

def mostrar(sem, titulo):
    print(f"\n  ── {titulo} ──")
    sem.generador.fila.imprimir()


print("\n" + "═"*55)
print("  BLOQUE 1 — ESTRUCTURAS: PILAS Y FILA")
print("═"*55 + "\n")

# TC-C-01
p = PilaOperandos()
assert p.vacia()
p.push('x'); p.push('y'); p.push('3')
assert p.top() == '3' and p.pop() == '3' and p.pop() == 'y' and not p.vacia()
print("  [TC-C-01] ✓ PASA — PilaOperandos: push/pop/top/vacia")

# TC-C-02
p = PilaOperadores()
p.push('+'); p.push('*')
assert p.top() == '*' and p.pop() == '*' and p.pop() == '+' and p.vacia()
print("  [TC-C-02] ✓ PASA — PilaOperadores: push/pop/top/vacia")

# TC-C-03
p = PilaTipos()
p.push('entero'); p.push('flotante')
assert p.pop() == 'flotante' and p.pop() == 'entero' and p.vacia()
print("  [TC-C-03] ✓ PASA — PilaTipos: push/pop/top/vacia")

# TC-C-04
f = FilaCuadruplos()
idx = f.encolar(Cuadruplo('+', 'x', 'y', 't1'))
f.encolar(Cuadruplo('=', 't1', None, 'z'))
assert idx == 0 and f.tamanio() == 2
assert f.ver(0).operador == '+' and f.ver(1).resultado == 'z'
print("  [TC-C-04] ✓ PASA — FilaCuadruplos: encolar/ver/tamanio")


print("\n" + "═"*55)
print("  BLOQUE 2 — EXPRESIONES ARITMÉTICAS")
print("═"*55)

# TC-C-05
sem = analizar("programa t;\nvars\n    x : entero;\ninicio\n    x = 5;\nfin")
c = list(sem.generador.fila)
assert c[0].operador == '=' and c[0].operando1 == '5' and c[0].resultado == 'x'
print("\n  [TC-C-05] ✓ PASA — Asignación simple: x = 5")
mostrar(sem, "x = 5")

# TC-C-06
sem = analizar("programa t;\nvars\n    x, a, b : entero;\ninicio\n    x = a + b;\nfin")
c = list(sem.generador.fila)
assert c[0].operador == '+' and c[1].operador == '='
print("\n  [TC-C-06] ✓ PASA — Suma: x = a + b")
mostrar(sem, "x = a + b")

# TC-C-07
sem = analizar("programa t;\nvars\n    x, y : entero;\ninicio\n    x = 3 + y * 2;\nfin")
c = list(sem.generador.fila)
assert c[0].operador == '*', f"Esperaba '*' primero, obtuve '{c[0].operador}'"
assert c[1].operador == '+' and c[2].operador == '='
print("\n  [TC-C-07] ✓ PASA — Precedencia: x = 3 + y * 2  (* antes que +)")
mostrar(sem, "x = 3 + y * 2")

# TC-C-08
sem = analizar("programa t;\nvars\n    x, a, b, c : entero;\ninicio\n    x = (a + b) * c;\nfin")
c = list(sem.generador.fila)
assert c[0].operador == '+' and c[1].operador == '*'
print("\n  [TC-C-08] ✓ PASA — Paréntesis: x = (a + b) * c")
mostrar(sem, "x = (a + b) * c")

# TC-C-09
sem = analizar("programa t;\nvars\n    x : entero;\ninicio\n    x = -5;\nfin")
ops = [c.operador for c in sem.generador.fila]
assert 'UMINUS' in ops
print("\n  [TC-C-09] ✓ PASA — Signo unario: x = -5")
mostrar(sem, "x = -5")

# TC-C-10
sem = analizar("programa t;\nvars\n    r : flotante;\n    a : entero;\n    b : flotante;\ninicio\n    r = a + b;\nfin")
assert len(sem.errores) == 0
print("\n  [TC-C-10] ✓ PASA — Tipos: entero + flotante (sin errores de tipo)")
mostrar(sem, "r = a + b  (entero + flotante)")


print("\n" + "═"*55)
print("  BLOQUE 3 — ESTATUTOS LINEALES COMPLETOS")
print("═"*55)

# TC-C-11
sem = analizar("programa t;\nvars\n    x, y : entero;\ninicio\n    si (x > 0) { y = 1; }\nfin")
ops = [c.operador for c in sem.generador.fila]
assert '>' in ops and '=' in ops
print("\n  [TC-C-11] ✓ PASA — Condicional: si (x > 0) { y = 1; }")
mostrar(sem, "si (x > 0)")

# TC-C-12
sem = analizar("programa t;\nvars\n    i : entero;\ninicio\n    mientras (i < 10) haz { i = i + 1; };\nfin")
ops = [c.operador for c in sem.generador.fila]
assert '<' in ops
print("\n  [TC-C-12] ✓ PASA — Ciclo: mientras (i < 10) haz { i = i + 1; }")
mostrar(sem, "mientras (i < 10)")

# TC-C-13
sem = analizar('programa t;\nvars\n    x : entero;\ninicio\n    x = 3;\n    escribe(x, "listo");\nfin')
ops = [c.operador for c in sem.generador.fila]
assert 'PRINT' in ops
print('\n  [TC-C-13] ✓ PASA — Imprime: escribe(x, "listo")')
mostrar(sem, 'escribe(x, "listo")')

# TC-C-14
sem = analizar("""
programa t;
vars
    n : entero;
nula calcular(x : entero) {
    n = x;
};
inicio
    calcular(5);
fin""")
ops = [c.operador for c in sem.generador.fila]
assert 'CALL' in ops
print("\n  [TC-C-14] ✓ PASA — Llamada: calcular(5)")
mostrar(sem, "calcular(5)")

# TC-C-15: programa integrador
sem = analizar("""
programa factorial;
vars
    n, resultado : entero;
inicio
    n = 5;
    resultado = 1;
    mientras (n > 0) haz {
        resultado = resultado * n;
        n = n - 1;
    };
    escribe(resultado, " es el factorial");
fin""")
assert len(sem.errores) == 0
print("\n  [TC-C-15] ✓ PASA — Programa integrador: factorial")
mostrar(sem, "factorial completo")

print("\n" + "═"*55)
print("  Todos los casos pasaron ✓")
print("═"*55 + "\n")