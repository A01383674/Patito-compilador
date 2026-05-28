"""
memoria.py  –  Administrador de direcciones virtuales para el compilador Patito.

Rangos asignados:
  global   entero   :  1000 – 1999
  global   flotante :  2000 – 2999
  local    entero   :  3000 – 3999
  local    flotante :  4000 – 4999
  temp     entero   :  5000 – 5999
  temp     flotante :  6000 – 6999
  constante entero  :  7000 – 7999
  constante flotante:  8000 – 8999
  constante cadena  :  9000 – 9999
"""

class MemoriaVirtual:
    RANGOS = {
        'global':    {'entero': (1000, 1999), 'flotante': (2000, 2999)},
        'local':     {'entero': (3000, 3999), 'flotante': (4000, 4999)},
        'temp':      {'entero': (5000, 5999), 'flotante': (6000, 6999)},
        'constante': {'entero': (7000, 7999), 'flotante': (8000, 8999),
                      'cadena': (9000, 9999)},
    }

    def __init__(self):
        # Contadores actuales: se inicializan al inicio del rango
        self._cont = {
            seg: {t: r[0] for t, r in tipos.items()}
            for seg, tipos in self.RANGOS.items()
        }
        # Pool de constantes:  (valor_str, tipo) -> dirección virtual
        self._pool: dict = {}

    # ── Asignación ────────────────────────────────────────────────────────────

    def asignar(self, segmento: str, tipo: str) -> int:
        """Asigna y retorna la próxima dirección libre en el segmento/tipo dado."""
        inicio, limite = self.RANGOS[segmento][tipo]
        actual = self._cont[segmento][tipo]
        if actual > limite:
            raise OverflowError(
                f"Segmento '{segmento}/{tipo}' agotado (límite {limite})"
            )
        self._cont[segmento][tipo] += 1
        return actual

    def asignar_constante(self, valor: str, tipo: str) -> int:
        """
        Si la constante ya tiene dirección la reutiliza;
        si no, asigna una nueva en el segmento 'constante'.
        """
        clave = (valor, tipo)
        if clave not in self._pool:
            self._pool[clave] = self.asignar('constante', tipo)
        return self._pool[clave]

    # ── Gestión de scopes ─────────────────────────────────────────────────────

    def reiniciar_local(self):
        """Reinicia el segmento local al inicio de cada nueva función."""
        for t in ('entero', 'flotante'):
            self._cont['local'][t] = self.RANGOS['local'][t][0]

    # ── Consulta ──────────────────────────────────────────────────────────────

    def tipo_de_dir(self, dir_: int) -> tuple:
        """Retorna (segmento, tipo) para una dirección, o (None, None)."""
        for seg, tipos in self.RANGOS.items():
            for tipo, (ini, fin) in tipos.items():
                if ini <= dir_ <= fin:
                    return seg, tipo
        return None, None

    def pool_constantes(self) -> dict:
        """Retorna el pool como {dirección: (valor, tipo)}."""
        return {d: kv for kv, d in self._pool.items()}

    # ── Impresión ─────────────────────────────────────────────────────────────

    def imprimir(self):
        print(f"\n  {'SEGMENTO':<12} {'TIPO':<10} {'INICIO':<8} {'USADAS':<8} LÍMITE")
        print(f"  {'-'*52}")
        for seg in ('global', 'local', 'temp', 'constante'):
            for tipo, (ini, fin) in self.RANGOS[seg].items():
                usadas = self._cont[seg][tipo] - ini
                if usadas:
                    print(f"  {seg:<12} {tipo:<10} {ini:<8} {usadas:<8} {fin}")

        if self._pool:
            print(f"\n  {'DIR':<8} {'TIPO':<10} VALOR")
            print(f"  {'-'*35}")
            for (val, tipo), dir_ in sorted(self._pool.items(), key=lambda x: x[1]):
                print(f"  {dir_:<8} {tipo:<10} {val}")
