# 08/09/2022
* Se agrega filtro para entorno multiempresa en de certificado y servidor dentro de la empresa.
* Se mejora filtro en lineas de factura de venta, el tipo de impuesto de venta ya no se muestra en facturas de compra

# 13/09/2022
* Se establece un codigo de producto para el xml en caso el producto no cuente con uno y asi evitar enviar "-" que actualmente "devuelve aceptado con observaciones"
* Se actualiza la funcion "_ agregar_informacion_empresa" para tomar los datos desde una funcion, esto sirve para el modulo de multisucursal

* Se agrega configuracion para poder visualizar los montos totales de exonerados y demas tanto en el formulario como en la impresion (se tiene que modificar el grupo de tipo de impuesto activando el check "Mostrar base" de los registros que se requieran)

# 14/09/2022
* Se mejora la visualizacion del tipo de cambio dolar en la factura

# 02/10/2022
* Se arregla bug con el codigo de producto que se envia en el xml
* Se arregla bug que se tenia en algunos casos con el redondeo de la detracciones que se envia en el xml

# 07/10/2022
* Se arregla bug al ocultar/mostrar el tipo de documento en factura cuando se ingresa desde ventas

# 14/10/2022
* Se modifica reporte de factura para enlazar mejor con el modulo de guias electronicas
* Se valida factuas con detraccion en soles y dolares, asi como al contado y credito

# 18/11/2022
* Se modifica forma de leer el xml de la vista, con esto se logra poder heredar la funcion y modificar sin problema en otro modulo dependiente (solse_pe_purchase).

# 30/11/2022
* Se soluciona bug en notas de credito que tenian como origen facturas con descuento.

# 10/11/2022
* Se soluciona bug al visualizar monto de operacion gravada cuando es en dolares

# 18/11/2022
* Se mejora la interfaz que mostraba el tipo de documento cuando no se estaba en el grupo de contabilidad completa

# 22/12/2022
* Se agrega campo que se usara en el modulo solse_pe_cpe_pos_offline y que sirve para gestionar facturas creadas en modo offline

# 27/12/2022
* Se agrega función para validación de envió, útil para otros módulos que dependen de este.

# 06/12/2022
* Se soluciona bug al emitir notas de credito con items con cantidades mayores a 1.
* Se soluciona bug al instalar el modulo usando libreria de python >= 3.9 (libreria base64)