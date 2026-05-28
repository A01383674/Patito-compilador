import sys
from lark import exceptions
from patito_parser import crear_parser
from semantica import AnalizadorSemantico


def compilar(codigo: str):
    parser = crear_parser()

    # ── Etapa 1: Análisis léxico y sintáctico ─────────────────────────────────
    try:
        arbol = parser.parse(codigo)
        print("✓ Análisis léxico y sintáctico exitoso")
    except exceptions.UnexpectedCharacters as e:
        print(f"✗ Error léxico en línea {e.line}, col {e.column}: "
              f"carácter inesperado '{e.char}'")
        return None
    except exceptions.UnexpectedToken as e:
        print(f"✗ Error sintáctico en línea {e.line}, col {e.column}: "
              f"token inesperado '{e.token}' (tipo: {e.token.type})")
        return None
    except exceptions.UnexpectedEOF:
        print("✗ Error: fin de archivo inesperado.")
        return None

    # ── Etapa 2: Análisis semántico y generación de cuádruplos ───────────────
    semantico = AnalizadorSemantico()
    ok = semantico.analizar(arbol)

    if ok:
        semantico.imprimir_todo()

    return arbol, semantico


def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else "pruebas/test_simple.patito"
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            codigo = f.read()
    except FileNotFoundError:
        print(f"✗ No se encontró el archivo: {ruta}")
        sys.exit(1)

    print(f"\n── Compilando: {ruta} ──")
    compilar(codigo)


if __name__ == "__main__":
    main()