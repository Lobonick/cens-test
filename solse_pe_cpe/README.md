# Datos de version
* El campo "display_type" en la tabla account_move_line ahora es obligatorio

### Documentación para Facturas::: https://cpe.sunat.gob.pe/sites/default/files/inline-files/guia%2Bxml%2Bfactura%2Bversion%202-1%2B1%2B0%20%282%29_0.pdf

# 17 Código del domicilio fiscal o de local anexo del emisor.
# 18 Tipo y número de documento de identidad del adquirente o usuario. 
# 19 Apellidos y nombres o denominación o razón social del adquirente o
usuario. 
# 20 Dirección del lugar en el que se entrega el bien. 
# 21 Descuentos Globales.

# 22 Monto Total de Impuestos.
# 23 Total valor de venta - operaciones gravadas.
# 24 Total valor de venta - operaciones exoneradas.
# 25 Total valor de venta - operaciones inafectas
# 26 Total Valor de Venta de Operaciones gratuitas. 
	Este elemento, se utilizará cuando exista transferencia de bienes o de servicios que se
	realice gratuitamente. Representa la sumatoria de los ítems, que correspondan a
	operaciones gratuitas, identificados con el elemento o tag descrito en el punto 39.
	Es decir, además del tag o campo indicado en el punto 39, se deberá consignar el Total
	Valor de venta de las operaciones gratuitas.
# 27 Sumatoria IGV
# 28 Sumatoria ISC.
# 29 Sumatoria otros tributos
# 30 Total Valor de Venta. 
# 31 Total Precio de Venta. 
# 32 Total de Descuentos
	A través de este elemento se debe indicar el valor total de los descuentos globales
	realizados de ser el caso.
	Este elemento es distinto al elemento Descuentos Globales definido en el punto 35. Su
	propósito es permitir consignar en el comprobante de pago:
	 la sumatoria de los descuentos de cada línea (descuentos por ítem), o
	 la sumatoria de los descuentos de línea (ítem) + descuentos globale
# 33 Sumatoria otros Cargos.
# 34 Importe total de la venta, de la cesión en uso o del servicio prestado. 

# 35 Número de orden del Ítem
# 36 Cantidad y Unidad de Medida por ítem
# 37 Valor de venta por ítem
	Obligatorio. Este elemento es el producto de la cantidad por el valor unitario (Q x Valor
	Unitario) y la deducción de los descuentos aplicados a dicho ítem (de existir).
	Este importe no incluye los tributos (IGV, ISC y otros Tributos), los descuentos globales o
	cargos
# 38 Precio de venta unitario por ítem y código.
	Obligatorio.Dentro del ámbito tributario, es el monto correspondiente al precio unitario
	facturado del bien vendido o servicio vendido. Este monto es la suma total que queda
	obligado a pagar el adquirente o usuario por cada bien o servicio. Esto incluye los tributos
	(IGV, ISC y otros Tributos) y la deducción de descuentos por ítem. Para identificar este
	monto se debe consignar el código “01” (Catálogo No. 16).
# 39 Valor referencial unitario por ítem en operaciones no onerosas
	Cuando la transferencia de bienes o de servicios se efectúe gratuitamente, se consignará
	el importe del valor de venta unitario que hubiera correspondido a dicho bien o servicio, en
	operaciones onerosas con terceros. En su defecto se aplicará el valor de mercado.
	Para identificar este valor, se debe de consignar el código “02” (incluido en el Catálogo No.
	16).
# 40 Descuentos por ítem
	Su propósito es permitir consignar en el comprobante de pago, un descuento a nivel de
	línea o ítem.
# 41 Cargos por ítem
	Su propósito es permitir consignar en el comprobante de pago, un cargo a nivel de línea o ítem.
# 42 Afectación al IGV por ítem
# 43 Sistema de ISC por ítem
# 44 Descripción detallada. 
	Obligatorio. Descripción detallada del servicio prestado, bien vendido o cedido en uso,
	indicando el nombre y las características, tales como marca del bien vendido o cedido en
	uso.
	Otras consideraciones:
	 Se deberá colocar el número de serie y/o número de motor, si se trata de un bien
	identificable, de corresponder, salvo que no fuera posible su consignación al momento
	de la emisión del comprobante de pago.
	 Tratándose de la venta de medicamentos y/o insumos para tratamiento de
	enfermedades oncológicas y del VIH/SIDA, se consignará adicionalmente la(s)
	partida(s) arancelaria(s) correspondiente(s). En este casoel comprobante de pago no
	podrá incluir bienes que no sean materia de dicho beneficio.
	 Si el emisor electrónico lleva por lo menos un Registro de Inventario Permanente en
	Unidades Físicas, al amparo de las normas del Impuesto a la Renta, podrá consignar en
	reemplazo de la descripción detallada, la descripción requerida por el Reglamento de
	Comprobantes de Pago para las facturas, en la medida que añada el código que
	las normas que regulan el llevado de libros y registros denominan como código de
	existencia.
# 45 Código de producto del Ítem. 
	Opcional. Código del producto de acuerdo al tipo de codificación interna que se utilice.
	Su uso será obligatorio si el emisor electrónico, opta por consignar este código, en
	reemplazo de la descripción detallada. Para tal efecto el código a usar será aquél, que las
	normas que regulan el llevado de libros y registros, denominan como código de existencia.
# 46 Código de producto SUNAT. 
	Opcional. Código del producto de acuerdo al estándar internacional de la ONU denominado:
	United Nations Standard Products and Services Code - Código de productos y servicios
	estándar de las Naciones Unidas - UNSPSC v14_0801, a que hace referencia el catálogo N°
	15 del Anexo N° 8 de la Resolución de Superintendencia N° 097-2012/SUNAT y
	modificatorias
# 47 Propiedades Adicionales del Ítem
	A través de este elemento se podrá indicar información adicional al ítem el cual es materia
	de comunicación. A su vez tiene diferentes elementos que se usaran de acuerdo a lo que
	corresponda informar. Para tal caso tener en cuenta el último párrafo del presente numeral. 
# 48 Valor unitario por ítem. 
	Obligatorio. Se consignará el importe correspondiente al valor o monto unitario del bien
	vendido, cedido o servicio prestado, indicado en una línea o ítem de la factura. Este importe no
	incluye los tributos (IGV, ISC y otros Tributos) ni los cargos globales. Ubicación

	