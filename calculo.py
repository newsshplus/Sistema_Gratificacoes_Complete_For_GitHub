
def calcular_gratificacao(vendas, meta_min, meta_100, grat_100, bonus_pct):
    # Inputs: numeric values (floats). If meta values missing, return zeros.
    if vendas is None or meta_100 is None or grat_100 is None:
        return {'atingimento': None, 'grat_base': 0.0, 'bonus': 0.0, 'total': 0.0}
    if meta_100 == 0:
        return {'atingimento': 0.0, 'grat_base': 0.0, 'bonus': 0.0, 'total': 0.0}
    atingimento = vendas / meta_100
    # If below meta_min -> 0
    if meta_min is not None and vendas < meta_min:
        return {'atingimento': round(atingimento,4), 'grat_base': 0.0, 'bonus': 0.0, 'total': 0.0}
    # Gratificação base: proportional up to 100% of grat_100
    proporcao = min(atingimento, 1.0)
    grat_base = proporcao * grat_100
    # Bonus on exceeding 100%: bonus_pct * (vendas - meta_100)
    bonus = 0.0
    if vendas > meta_100 and bonus_pct is not None:
        bonus = (vendas - meta_100) * bonus_pct
    total = round(grat_base + bonus,2)
    return {'atingimento': round(atingimento,4), 'grat_base': round(grat_base,2), 'bonus': round(bonus,2), 'total': total}
