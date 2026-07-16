"""
Corte de buffers (buffer cutting).

Del plano se lee HKP = distancia entre el sticker de la cabina y el buffer de la
cabina cuando la cabina sirve el primer nivel. El usuario mide en obra el valor
real HKPR de cada buffer. El corte de cada buffer es:

    CutBuffer = HKP − HKPR

Todo en mm. Si CutBuffer < 0, no hay nada que cortar (el buffer real ya queda por
debajo del teórico → revisar en obra), se marca como aviso.
"""


def compute_buffer_cut(hkp: float, hkpr_list: list) -> dict:
    """hkp: valor del plano. hkpr_list: HKPR real de cada buffer.
    Devuelve {'HKP', 'buffers':[{'n','HKPR','CutBuffer','warn'}]}."""
    hkp = float(hkp or 0)
    buffers = []
    for i, hkpr in enumerate(hkpr_list, start=1):
        v = float(hkpr or 0)
        cut = round(hkp - v, 1)
        buffers.append({"n": i, "HKPR": v, "CutBuffer": cut, "warn": cut < 0})
    return {"HKP": hkp, "buffers": buffers}
