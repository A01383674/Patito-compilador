from patito_parser import crear_parser

PALABRAS_RESERVADAS = [
    "PROGRAMA", "INICIO", "FIN", "VARS_KW",
    "MIENTRAS", "HAZ", "SI", "SINO",
    "ESCRIBE", "NULA", "ENTERO", "FLOTANTE",
]
TIPOS_DE_DATO              = ["ENTERO", "FLOTANTE"]
IDENTIFICADORES_CONSTANTES = ["ID", "CTE_ENT", "CTE_FLOT", "LETRERO"]
OPERADORES_ARITMETICOS     = ["MAS", "MENOS", "MULT", "DIV", "ASIGNA"]
OPERADORES_RELACIONALES    = ["MENOR_QUE", "MAYOR_QUE", "IGUAL_IGUAL", "DIFERENTE"]
DELIMITADORES              = [
    "PUNTO_COMA", "COMA", "DOS_PUNTOS",
    "PAR_ABRE", "PAR_CIERRA", "LLAVE_ABRE", "LLAVE_CIERRA",
]
TODOS_LOS_TOKENS = (
    PALABRAS_RESERVADAS + IDENTIFICADORES_CONSTANTES +
    OPERADORES_ARITMETICOS + OPERADORES_RELACIONALES + DELIMITADORES
)

def tokenizar(codigo: str) -> list:
    """Retorna lista de Token con .type y .value."""
    parser = crear_parser()
    return list(parser.lex(codigo))

def imprimir_tokens(codigo: str) -> None:
    tokens = tokenizar(codigo)
    print(f"{'TIPO':<20} VALOR")
    print("-" * 35)
    for t in tokens:
        print(f"{t.type:<20} {repr(t)}")