#from datetime import datetime
from datetime import datetime, date, timedelta

ngr_fecha  = date(2024, 2, 1)
cese_fecha = date(2025, 4, 2)
ajus_fecha_original = cese_fecha
ultimo_dia_mes = ultimo_dia_del_mes(cese_fecha)
w_pase = True
w_cont = 0
max_iterations = 1000  # Protección contra bucles infinitos

while w_pase and w_cont < max_iterations:
    w_cont += 1
    ajus_fecha_original = ajus_fecha_original - timedelta(days=1)  # Usar timedelta para restar días
    ajus_anio = ajus_fecha_original.year 
    top1_param = date(ajus_anio, 5, 1)
    top2_param = date(ajus_anio, 11, 1)
    
    if (ajus_fecha_original == top1_param) or (ajus_fecha_original == top2_param):
        break
        
    if w_cont % 50 == 0:  # Para no imprimir demasiadas líneas, mostrar cada 50 iteraciones
        print(f'Iteración {w_cont}: Fecha {ajus_fecha_original}, Top1: {top1_param}, Top2: {top2_param}')

print(f'Iteraciones totales: {w_cont}')
print(f'Último día del mes : {ultimo_dia_mes}')
print(f'RESULTADO (original): {ajus_fecha_original}')


def ultimo_dia_del_mes(fecha):
    primer_dia_del_mes = fecha.replace(day=1)
    ultimo_dia_del_mes = primer_dia_del_mes + datetime.timedelta(days=31)
    return ultimo_dia_del_mes - datetime.timedelta(days=1)
