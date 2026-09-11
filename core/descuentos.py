# Códigos de descuento válidos. Los porcentajes NO deben gestionarse en el
# frontend; aquí es la única fuente de verdad para el servidor.

CODIGOS_DESCUENTO = {
    'DESC10': 10,
    'DESCUENTO10': 10,
    'PROMO20': 20,
    'SUPER30': 30,
    'OFERTA50': 50,
}


def porcentaje_codigo(codigo):
    """Devuelve el porcentaje asociado a un código, o 0 si no es válido."""
    if not codigo:
        return 0
    return CODIGOS_DESCUENTO.get(str(codigo).strip().upper(), 0)