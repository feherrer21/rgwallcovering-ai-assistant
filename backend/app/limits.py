"""Límite de peticiones por IP para POST /chat.

Un diccionario en memoria, no Redis: el tráfico es el de la web de un negocio
de cinco personas y el proceso es uno solo. Si algún día hay dos réplicas, el
límite se aplicará por réplica —para lo que protege esto, sigue sirviendo.

Lo que protege es el presupuesto de API de Ronald: cada turno de /chat es una
llamada al modelo que él paga (03_spec.md §8).
"""

import time
from collections import defaultdict, deque

MINUTO = 60
HORA = 3600

#: A partir de cuántas IPs distintas se barren las que ya caducaron. El barrido
#: es O(n) y no hace falta hacerlo en cada petición.
_UMBRAL_BARRIDO = 500


class Limitador:
    """Ventana deslizante doble: por minuto y por hora."""

    def __init__(self, por_minuto: int, por_hora: int) -> None:
        self.por_minuto = por_minuto
        self.por_hora = por_hora
        self._visitas: dict[str, deque[float]] = defaultdict(deque)

    def permitido(self, ip: str) -> tuple[bool, int]:
        """¿Puede esta IP hacer una petición ahora?

        Devuelve (permitido, segundos_de_espera). Los segundos son para la
        cabecera `Retry-After`: decirle a alguien que espere sin decirle
        cuánto es una forma de no decirle nada.
        """
        ahora = time.monotonic()

        if len(self._visitas) > _UMBRAL_BARRIDO:
            self._barrer(ahora)

        visitas = self._visitas[ip]
        while visitas and ahora - visitas[0] > HORA:
            visitas.popleft()

        en_el_minuto = sum(1 for t in visitas if ahora - t <= MINUTO)

        if en_el_minuto >= self.por_minuto:
            mas_antigua = next(t for t in visitas if ahora - t <= MINUTO)
            return False, max(1, int(MINUTO - (ahora - mas_antigua)) + 1)

        if len(visitas) >= self.por_hora:
            return False, max(1, int(HORA - (ahora - visitas[0])) + 1)

        visitas.append(ahora)
        return True, 0

    def _barrer(self, ahora: float) -> None:
        """Descarta las IPs sin visitas en la última hora."""
        caducadas = [
            ip
            for ip, visitas in self._visitas.items()
            if not visitas or ahora - visitas[-1] > HORA
        ]
        for ip in caducadas:
            del self._visitas[ip]
