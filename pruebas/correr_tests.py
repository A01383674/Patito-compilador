import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lark import exceptions
from patito_parser import crear_parser

parser = crear_parser()

def caso_ok(id_, descripcion, codigo):
    try:
        parser.parse(codigo)
        print(f"  [{id_}] ✓ PASA — {descripcion}")
    except Exception as e:
        print(f"  [{id_}] ✗ FALLA — {descripcion}")
        print(f"         {e}")

def tokens(codigo):
    return [t.type for t in parser.lex(codigo)]

def caso_tokens(id_, descripcion, codigo, token_esperado, cantidad):
    try:
        lista  = tokens(codigo)
        conteo = lista.count(token_esperado)
        if conteo == cantidad:
            print(f"  [{id_}] ✓ PASA — {descripcion}")
            print(f"         {token_esperado} encontrado {conteo} vez/veces")
        else:
            print(f"  [{id_}] ✗ FALLA — {descripcion}")
            print(f"         Se esperaban {cantidad} de {token_esperado}, se encontraron {conteo}")
    except Exception as e:
        print(f"  [{id_}] ✗ FALLA — {type(e).__name__}: {e}")


print("  CASOS DE PRUEBA — ANÁLISIS LÉXICO")
print("-----------------------------------\n")

caso_tokens("TC-L-01", "Todas las palabras reservadas",
    "programa inicio fin vars mientras haz si sino escribe nula entero flotante",
    "PROGRAMA", 1)
try:
    lista = tokens("programa inicio fin vars mientras haz si sino escribe nula entero flotante")
    reservadas = ['PROGRAMA','INICIO','FIN','VARS_KW','MIENTRAS','HAZ',
                  'SI','SINO','ESCRIBE','NULA','ENTERO','FLOTANTE']
    faltantes = [r for r in reservadas if r not in lista]
    if not faltantes:
        print("         Todas las 12 palabras reservadas reconocidas")
    else:
        print(f"         Faltaron: {faltantes}")
except Exception as e:
    print(f"         Error: {e}")

caso_tokens("TC-L-02", "Identificadores válidos",
    "miVar _temp contador x1 __aux nombreLargo123", "ID", 6)

print("\n  Probando TC-L-03...")
try:
    parser.parse("programa t; inicio\n    1variable = 5;\nfin")
    print("  [TC-L-03] ✗ FALLA — Se esperaba error pero parseó sin problemas")
except (exceptions.UnexpectedToken, exceptions.UnexpectedCharacters):
    print("  [TC-L-03] ✓ PASA — '1variable' rechazado correctamente")

caso_tokens("TC-L-04", "Constantes enteras",
    "0  42  999  1000000", "CTE_ENT", 4)

print("\n  Probando TC-L-05...")
try:
    lista  = tokens("3.14  0.5  100.001")
    floats = lista.count("CTE_FLOT")
    ents   = lista.count("CTE_ENT")
    if floats == 3 and ents == 0:
        print("  [TC-L-05] ✓ PASA — 3 tokens CTE_FLOT, 0 CTE_ENT")
    else:
        print(f"  [TC-L-05] ✗ FALLA — CTE_FLOT={floats}, CTE_ENT={ents}")
except Exception as e:
    print(f"  [TC-L-05] ✗ FALLA — {e}")


print("  CASOS DE PRUEBA — ANÁLISIS SINTÁCTICO")
print("-----------------------------------\n")

caso_ok("TC-P-01", "Programa mínimo",
    "programa vacio;\ninicio\nfin")

caso_ok("TC-P-02", "Declaración de variables",
    "programa t;\nvars\n    x, y : entero;\n    pi : flotante;\ninicio\n    x = 0;\nfin")

caso_ok("TC-P-03", "Asignación con expresión aritmética",
    "programa t;\nvars\n    x, y : entero;\ninicio\n    x = 3 + y * 2;\nfin")

caso_ok("TC-P-04", "Condicional sin sino",
    "programa t;\nvars\n    x, y : entero;\ninicio\n    si (x > 0) { y = 1; }\nfin")

caso_ok("TC-P-05", "Condicional con sino",
    "programa t;\nvars\n    x, y : entero;\ninicio\n    si (x > 0) { y = 1; } sino { y = -1; }\nfin")

print("\n-----------------------------------\n")