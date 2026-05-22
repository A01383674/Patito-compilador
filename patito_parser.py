import os
from lark import Lark

def crear_parser() -> Lark:
    ruta_gramatica = os.path.join(os.path.dirname(__file__), "grammar.lark")
    with open(ruta_gramatica, "r", encoding="utf-8") as f:
        gramatica = f.read()
    return Lark(
        gramatica,
        start="programa",
        parser="earley",
        propagate_positions=True
    )