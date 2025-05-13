
## Prompt Log Entry - 2025-05-08 15:17:48

### System Message
```
You are a meticulous Spanish invoice parser. Your job is to extract structured data from invoice OCR text according to a specific schema.

# Schema
The extracted data must conform to this schema:
```json
{
  "properties": {
    "buyer_name": {
      "description": "Name of the company or person receiving the invoice",
      "type": "string"
    },
    "buyer_tax_id": {
      "description": "Tax identification number (NIF/CIF) of the buyer",
      "pattern": "^[A-Z0-9]\\d{7}[A-Z0-9]$",
      "type": "string"
    },
    "currency": {
      "description": "Currency used in the invoice",
      "enum": [
        "EUR"
      ],
      "type": "string"
    },
    "invoice_number": {
      "description": "Invoice identification number",
      "type": "string"
    },
    "invoice_type": {
      "description": "Type of invoice (standard, simplified, rectification, etc.)",
      "enum": [
        "standard",
        "simplified",
        "rectification",
        "credit_note"
      ],
      "type": "string"
    },
    "issue_date": {
      "description": "Date when the invoice was issued in DD/MM/YYYY format",
      "pattern": "^[0-3][0-9]/[0-1][0-9]/[0-9]{4}$",
      "type": "string"
    },
    "line_items": {
      "description": "Individual line items on the invoice",
      "items": {
        "properties": {
          "description": {
            "description": "Description of the product or service",
            "type": "string"
          },
          "line_total": {
            "description": "Total price for this line item in EUR",
            "type": "string"
          },
          "qty": {
            "description": "Quantity of items",
            "type": "string"
          },
          "unit_price": {
            "description": "Price per unit in EUR",
            "type": "string"
          }
        },
        "type": "object"
      },
      "type": "array"
    },
    "metadata": {
      "description": "Additional metadata about the extraction process",
      "type": "object"
    },
    "notes": {
      "description": "Additional notes or comments on the invoice",
      "type": "string"
    },
    "payment_terms": {
      "description": "Terms of payment (optional)",
      "type": "string"
    },
    "subtotal": {
      "description": "Subtotal amount before taxes",
      "pattern": "^[0-9]{1,3}(\\s?[0-9]{3})*(,[0-9]{2})?(\\s?\u20ac)?$",
      "type": "string"
    },
    "total_eur": {
      "description": "Total invoice amount in EUR currency",
      "pattern": "^[0-9]{1,3}(\\s?[0-9]{3})*(,[0-9]{2})?(\\s?\u20ac)?$",
      "type": "string"
    },
    "vat_amount": {
      "description": "VAT amount in EUR",
      "pattern": "^[0-9]{1,3}(\\s?[0-9]{3})*(,[0-9]{2})?(\\s?\u20ac)?$",
      "type": "string"
    },
    "vat_rate": {
      "description": "VAT percentage rate applied",
      "pattern": "^[0-9]{1,2}(,[0-9]{1,2})?%$",
      "type": "string"
    },
    "vendor_name": {
      "description": "Name of the company or person issuing the invoice",
      "type": "string"
    },
    "vendor_tax_id": {
      "description": "Tax identification number (NIF/CIF) of the vendor",
      "pattern": "^[A-Z0-9]\\d{7}[A-Z0-9]$",
      "type": "string"
    }
  },
  "required": [
    "invoice_number",
    "issue_date",
    "total_eur",
    "vat_rate",
    "vat_amount",
    "vendor_name",
    "vendor_tax_id",
    "buyer_name"
  ],
  "type": "object"
}
```

# Instructions
1. Extract all required fields and any available optional fields from the OCR text.
2. Normalize all extracted values to match the expected format in the schema.
3. For dates, ensure they are in DD/MM/YYYY format.
4. For currency amounts, keep the original format (with or without € symbol).
5. If you cannot find a required field, make your best guess and mark it with low confidence.
6. For line items, extract as many as you can identify.

<!--internal-->
# Analysis Process
1. First, identify the invoice structure and layout (header, items table, footer).
2. Look for key identifiers like "Factura", "Total", etc. to locate important sections.
3. Extract required fields first, then optional fields.
4. Validate data against the schema requirements.
5. Format the output as a valid JSON object.
<!--/internal-->

# Example Extractions

## Example 1

OCR Text:
```
EMPRESA EJEMPLO S.L.
C/ Ejemplo, 123
28001 Madrid, España
CIF: B12345678

FACTURA
Número: F2023-1234
Fecha: 15/06/2023

CLIENTE:
Cliente Ejemplo S.A.
C/ Cliente, 456
08001 Barcelona, España
CIF: A87654321

DESCRIPCIÓN          CANTIDAD    PRECIO     TOTAL
Servicio de consultoría      10     100,00 €   1000,00 €
Materiales de oficina         5      25,50 €    127,50 €
Soporte técnico              8      75,00 €    600,00 €

Base imponible:                             1727,50 €
IVA (21%):                                   362,78 €
TOTAL FACTURA:                              2090,28 €

Forma de pago: Transferencia bancaria
Vencimiento: 15/07/2023

Cuenta bancaria: ES12 3456 7890 1234 5678 9012
```

Correct Extraction:
```json
{
  "buyer_name": "Cliente Ejemplo S.A.",
  "buyer_tax_id": "A87654321",
  "invoice_number": "F2023-1234",
  "issue_date": "15/06/2023",
  "line_items": [
    {
      "description": "Servicio de consultor\u00eda",
      "line_total": "1000,00 \u20ac",
      "qty": "10",
      "unit_price": "100,00 \u20ac"
    },
    {
      "description": "Materiales de oficina",
      "line_total": "127,50 \u20ac",
      "qty": "5",
      "unit_price": "25,50 \u20ac"
    },
    {
      "description": "Soporte t\u00e9cnico",
      "line_total": "600,00 \u20ac",
      "qty": "8",
      "unit_price": "75,00 \u20ac"
    }
  ],
  "payment_terms": "Transferencia bancaria",
  "subtotal": "1727,50 \u20ac",
  "total_eur": "2090,28 \u20ac",
  "vat_amount": "362,78 \u20ac",
  "vat_rate": "21%",
  "vendor_name": "EMPRESA EJEMPLO S.L.",
  "vendor_tax_id": "B12345678"
}
```


## Example 2

OCR Text:
```
TECNOLOGÍA AVANZADA, S.A.
Avda. Innovación, 42
41092 Sevilla
NIF: A11223344

Factura Nº: TEC/2023/0089
Fecha de emisión: 22-03-2023

EMITIDO A:
Inversiones Futuras, S.L.
C/ Inversión, 78
28046 Madrid
NIF: B99887766

Concepto                      Unidades    P. unitario    Importe
---------------------------------------------------------------
Ordenador portátil HP Elite      2         899,00 €     1.798,00 €
Monitor 27" Dell UltraSharp     4         329,50 €     1.318,00 €
Servicio de instalación          1         250,00 €       250,00 €

Base imponible                                         3.366,00 €
IVA (21%)                                                706,86 €
TOTAL                                                  4.072,86 €

Condiciones de pago: 30 días mediante transferencia bancaria
Cuenta: ES98 7654 3210 9876 5432 1098
```

Correct Extraction:
```json
{
  "buyer_name": "Inversiones Futuras, S.L.",
  "buyer_tax_id": "B99887766",
  "invoice_number": "TEC/2023/0089",
  "issue_date": "22/03/2023",
  "line_items": [
    {
      "description": "Ordenador port\u00e1til HP Elite",
      "line_total": "1.798,00 \u20ac",
      "qty": "2",
      "unit_price": "899,00 \u20ac"
    },
    {
      "description": "Monitor 27\" Dell UltraSharp",
      "line_total": "1.318,00 \u20ac",
      "qty": "4",
      "unit_price": "329,50 \u20ac"
    },
    {
      "description": "Servicio de instalaci\u00f3n",
      "line_total": "250,00 \u20ac",
      "qty": "1",
      "unit_price": "250,00 \u20ac"
    }
  ],
  "payment_terms": "30 d\u00edas mediante transferencia bancaria",
  "subtotal": "3.366,00 \u20ac",
  "total_eur": "4.072,86 \u20ac",
  "vat_amount": "706,86 \u20ac",
  "vat_rate": "21%",
  "vendor_name": "TECNOLOG\u00cdA AVANZADA, S.A.",
  "vendor_tax_id": "A11223344"
}
```


## Example 3

OCR Text:
```
DISTRIBUCIONES MEDITERRÁNEAS, SL
Polígono Industrial Sur, Nave 15
46980 Valencia
CIF: B55667788

Cliente:
Hostelería Costa, SL
Avda. Playa, 123
03001 Alicante
CIF: B11335577

FACTURA Nº: DM-2023-0456
Fecha: 07/05/2023

Producto              Cant.   Precio/u    Total
-----------------------------------------
Aceite de oliva 5L      20     22,50      450,00
Vino tinto (caja 6)     15     32,00      480,00
Patatas (saco 25kg)     10     18,75      187,50

Subtotal:                             1.117,50
IVA 10%:                                111,75
TOTAL EUROS:                          1.229,25

Forma de pago: Recibo domiciliado
Vencimiento: 22/05/2023
```

Correct Extraction:
```json
{
  "buyer_name": "Hosteler\u00eda Costa, SL",
  "buyer_tax_id": "B11335577",
  "invoice_number": "DM-2023-0456",
  "issue_date": "07/05/2023",
  "line_items": [
    {
      "description": "Aceite de oliva 5L",
      "line_total": "450,00",
      "qty": "20",
      "unit_price": "22,50"
    },
    {
      "description": "Vino tinto (caja 6)",
      "line_total": "480,00",
      "qty": "15",
      "unit_price": "32,00"
    },
    {
      "description": "Patatas (saco 25kg)",
      "line_total": "187,50",
      "qty": "10",
      "unit_price": "18,75"
    }
  ],
  "payment_terms": "Recibo domiciliado",
  "subtotal": "1.117,50",
  "total_eur": "1.229,25",
  "vat_amount": "111,75",
  "vat_rate": "10%",
  "vendor_name": "DISTRIBUCIONES MEDITERR\u00c1NEAS, SL",
  "vendor_tax_id": "B55667788"
}
```



# Output Format
Respond ONLY with a valid JSON object containing all extracted fields, formatted according to the schema.
Do not include any explanations, notes, or additional text outside of the JSON object. 
```

### User Message
```
OCR Text:

Factura Pagado NO de referencia de pago 2suFZprY4TbarBvTOFSX Vendido por HONG KONG UGREEN LIMITED Fecha de la factura/Fecha de la entrega 28.04.2024 CARLOS LORENZO Número de la factura DS-ASE-INV-ES-2024-33264305 AVENIDA ISABEL DE VALOIS 90, BAJO A Total pendiente 69.99 € MADRID, MADRID, 28050 ES El IVA ha sido declarado Amazon Services Europe por S.a.r.L. IVA LU19647148 Si tienes preguntas sobre tus pedidos, visita https://www.amazon.es/contacto Dirección de facturación Dirección de envío Vendido por Carlos Lorenzo Carlos Lorenzo HONG KONG UGREEN LIMITED Avenida Isabel de Valois 90, Bajo A Avenida Isabel de Valois 90, Bajo A 19H WAN DI PLAZA Madrid, Madrid, 28050 Madrid, Madrid, 28050 3 TAI YU STREET, SAN PO KONG, KL ES ES HONG KONG, HONG KONG, 999077 HK Información del pedido Fecha del pedido 27.04.2024 Número del pedido 171-4544162-9429147 Detalles de la factura Descripción Cant. P. Unitario IVA % P. Unitario Precio total (IVA excluido) (IVA incluido) (IVA incluido) UGREEN Revodok Pro 210 Docking Station USB C 10 En 1 Doble HDMI 1 57,84 € 21% 69,99 € 69,99 € 8K30Hz 4K60Hz Hub Adaptador USB C a 2 HDMI Ethernet Gigabit USB 3.0 PD 100W Lector Tarjeta SD TF Compatible con MacBook Pro Air M2 M1 | BOBXDQS4BD Envío 0,00 € 0,00 € 0,00 € Total 69,99 € IVA % Precio total IVA (IVA excluido) 21% 57,84 € 12,15€ Total 57,84 € 12,15€
Factura Pagado NO de referencia de pago 2suFZprY4TbarBvTOFSX Vendido por Comfort Click Ltd Fecha de la factura/Fecha de la entrega 28.04.2024 CARLOS LORENZO Número de la factura DS-ASE-INV-ES-2024-33264321 AVENIDA ISABEL DE VALOIS 90, BAJO A Total pendiente 15,49 € MADRID, MADRID, 28050 ES El IVA ha sido declarado Amazon Services Europe por S.a.r.L. IVA LU19647148 Si tienes preguntas sobre tus pedidos, visita https://www.amazon.es/contacto Dirección de facturación Dirección de envío Vendido por Carlos Lorenzo Carlos Lorenzo Comfort Click Ltd Avenida Isabel de Valois 90, Bajo A Avenida Isabel de Valois 90, Bajo A 106 Lower Addiscombe Road Madrid, Madrid, 28050 Madrid, Madrid, 28050 CROYDON, Surrey, CRO 6AD ES ES GB Información del pedido Fecha del pedido 27.04.2024 Número del pedido 171-4544162-9429147 Detalles de la factura Descripción Cant. P. Unitario IVA % P. Unitario Precio total (IVA excluido) (IVA incluido) (IVA incluido) Vinagre de Sidra de Manzana con la Madre 1860mg de Potencia 180 1 14,08 € 10% 15,49 € 15,49 € Cápsulas Veganas - Con Probióticos, Cúrcuma, Jengibre y Pimienta de Cayena, Suplemento Dietético Natural Para 2 Meses | BO981NCGQPB Envío 0,00 € 0,00 € 0,00 € Total 15,49 € IVA % Precio total IVA (IVA excluido) 10% 14,08 € 1,41€ Total 14,08 € 1,41€

Initial fields extracted:

{
  "invoice_number": "1",
  "total_eur": "69,99",
  "vat_rate": "10%",
  "vat_amount": "1",
  "payment_terms": "2suFZprY4TbarBvTOFSX Vendido por HONG KONG UGREEN LIMITED Fecha de la factura/Fecha de la entrega 28.04.2024 CARLOS LORENZO Número de la factura DS - ASE - INV - ES - 2024 - 33264305 AVENIDA ISABEL DE VALOIS 90, BAJO A Total pendiente 69.99 € MADRID, MADRID, 28050 ES El IVA ha sido declarado Amazon Services Europe por S.a.r.L. IVA LU19647148 Si tienes preguntas sobre tus pedidos, visita https : //www.amazon.es/contacto Dirección de facturación Dirección de envío Vendido por Carlos Lorenzo Carlos Lorenzo HONG KONG UGREEN LIMITED Avenida Isabel de Valois 90, Bajo A Avenida Isabel de Valois 90, Bajo A 19H WAN DI PLAZA Madrid, Madrid, 28050 Madrid, Madrid, 28050 3 TAI YU STREET, SAN PO KONG, KL ES ES HONG KONG, HONG KONG, 999077 HK Información del pedido Fecha del pedido 27.04.2024 Número del pedido 171 - 4544162 - 9429147 Detalles de la factura Descripción Cant. P. Unitario IVA % P. Unitario Precio total (IVA excluido) (IVA incluido) (IVA incluido) UGREEN Revodok Pro 210 Docking Station USB C 10 En 1 Doble HDMI 1 57,84 € 21% 69,99 € 69,99 € 8K30Hz 4K60Hz Hub Adaptador USB C a 2 HDMI Ethernet Gigabit USB 3.0 PD 100W Lector Tarjeta SD TF Compatible con MacBook Pro Air M2 M1 | BOBXDQS4BD Envío 0,00 € 0,00 € 0,00 € Total 69,99 € IVA % Precio total IVA (IVA excluido) 21% 57,84 € 12,15€ Total 57,84 € 12,15€ Factura Pagado NO de referencia de pago 2suFZprY4TbarBvTOFSX Vendido por Comfort Click Ltd Fecha de la factura/Fecha de la entrega 28.04.2024 CARLOS LORENZO Número de la factura DS - ASE - INV - ES - 2024 - 33264321 AVENIDA ISABEL DE VALOIS 90, BAJO A Total pendiente 15,49 € MADRID, MADRID, 28050 ES El IVA ha sido declarado Amazon Services Europe por S.a.r.L. IVA LU19647148 Si tienes preguntas sobre tus pedidos, visita https : //www.amazon.es/contacto Dirección de facturación Dirección de envío Vendido por Carlos Lorenzo Carlos Lorenzo Comfort Click Ltd Avenida Isabel de Valois 90, Bajo A Avenida Isabel de Valois 90, Bajo A 106 Lower Addiscombe Road Madrid, Madrid, 28050 Madrid, Madrid, 28050 CROYDON, Surrey, CRO 6AD ES ES GB Información del pedido Fecha del pedido 27.04.2024 Número del pedido 171 - 4544162 - 9429147 Detalles de la factura Descripción Cant. P. Unitario IVA % P. Unitario Precio total (IVA excluido) (IVA incluido) (IVA incluido) Vinagre de Sidra de Manzana con la Madre 1860mg de Potencia 180 1 14,08 € 10% 15,49 € 15,49 € Cápsulas Veganas - Con Probióticos, Cúrcuma, Jengibre y Pimienta de Cayena, Suplemento Dietético Natural Para 2 Meses | BO981NCGQPB Envío 0,00 € 0,00 € 0,00 € Total 15,49 € IVA % Precio total IVA (IVA excluido) 10% 14,08 € 1,41€ Total 14,08 € 1,41€",
  "metadata": {
    "extraction_method": "regex_heuristics",
    "extraction_timestamp": "2025-05-08T15:17:48.654064"
  }
}
```

### Initial Fields
```json
{
  "invoice_number": "1",
  "total_eur": "69,99",
  "vat_rate": "10%",
  "vat_amount": "1",
  "payment_terms": "2suFZprY4TbarBvTOFSX Vendido por HONG KONG UGREEN LIMITED Fecha de la factura/Fecha de la entrega 28.04.2024 CARLOS LORENZO Número de la factura DS - ASE - INV - ES - 2024 - 33264305 AVENIDA ISABEL DE VALOIS 90, BAJO A Total pendiente 69.99 € MADRID, MADRID, 28050 ES El IVA ha sido declarado Amazon Services Europe por S.a.r.L. IVA LU19647148 Si tienes preguntas sobre tus pedidos, visita https : //www.amazon.es/contacto Dirección de facturación Dirección de envío Vendido por Carlos Lorenzo Carlos Lorenzo HONG KONG UGREEN LIMITED Avenida Isabel de Valois 90, Bajo A Avenida Isabel de Valois 90, Bajo A 19H WAN DI PLAZA Madrid, Madrid, 28050 Madrid, Madrid, 28050 3 TAI YU STREET, SAN PO KONG, KL ES ES HONG KONG, HONG KONG, 999077 HK Información del pedido Fecha del pedido 27.04.2024 Número del pedido 171 - 4544162 - 9429147 Detalles de la factura Descripción Cant. P. Unitario IVA % P. Unitario Precio total (IVA excluido) (IVA incluido) (IVA incluido) UGREEN Revodok Pro 210 Docking Station USB C 10 En 1 Doble HDMI 1 57,84 € 21% 69,99 € 69,99 € 8K30Hz 4K60Hz Hub Adaptador USB C a 2 HDMI Ethernet Gigabit USB 3.0 PD 100W Lector Tarjeta SD TF Compatible con MacBook Pro Air M2 M1 | BOBXDQS4BD Envío 0,00 € 0,00 € 0,00 € Total 69,99 € IVA % Precio total IVA (IVA excluido) 21% 57,84 € 12,15€ Total 57,84 € 12,15€ Factura Pagado NO de referencia de pago 2suFZprY4TbarBvTOFSX Vendido por Comfort Click Ltd Fecha de la factura/Fecha de la entrega 28.04.2024 CARLOS LORENZO Número de la factura DS - ASE - INV - ES - 2024 - 33264321 AVENIDA ISABEL DE VALOIS 90, BAJO A Total pendiente 15,49 € MADRID, MADRID, 28050 ES El IVA ha sido declarado Amazon Services Europe por S.a.r.L. IVA LU19647148 Si tienes preguntas sobre tus pedidos, visita https : //www.amazon.es/contacto Dirección de facturación Dirección de envío Vendido por Carlos Lorenzo Carlos Lorenzo Comfort Click Ltd Avenida Isabel de Valois 90, Bajo A Avenida Isabel de Valois 90, Bajo A 106 Lower Addiscombe Road Madrid, Madrid, 28050 Madrid, Madrid, 28050 CROYDON, Surrey, CRO 6AD ES ES GB Información del pedido Fecha del pedido 27.04.2024 Número del pedido 171 - 4544162 - 9429147 Detalles de la factura Descripción Cant. P. Unitario IVA % P. Unitario Precio total (IVA excluido) (IVA incluido) (IVA incluido) Vinagre de Sidra de Manzana con la Madre 1860mg de Potencia 180 1 14,08 € 10% 15,49 € 15,49 € Cápsulas Veganas - Con Probióticos, Cúrcuma, Jengibre y Pimienta de Cayena, Suplemento Dietético Natural Para 2 Meses | BO981NCGQPB Envío 0,00 € 0,00 € 0,00 € Total 15,49 € IVA % Precio total IVA (IVA excluido) 10% 14,08 € 1,41€ Total 14,08 € 1,41€",
  "metadata": {
    "extraction_method": "regex_heuristics",
    "extraction_timestamp": "2025-05-08T15:17:48.654064"
  }
}
```

---


## Prompt Log Entry - 2025-05-08 15:18:48

### System Message
```
You are a meticulous Spanish invoice parser. Your job is to extract structured data from invoice OCR text according to a specific schema.

# Schema
The extracted data must conform to this schema:
```json
{
  "properties": {
    "buyer_name": {
      "description": "Name of the company or person receiving the invoice",
      "type": "string"
    },
    "buyer_tax_id": {
      "description": "Tax identification number (NIF/CIF) of the buyer",
      "pattern": "^[A-Z0-9]\\d{7}[A-Z0-9]$",
      "type": "string"
    },
    "currency": {
      "description": "Currency used in the invoice",
      "enum": [
        "EUR"
      ],
      "type": "string"
    },
    "invoice_number": {
      "description": "Invoice identification number",
      "type": "string"
    },
    "invoice_type": {
      "description": "Type of invoice (standard, simplified, rectification, etc.)",
      "enum": [
        "standard",
        "simplified",
        "rectification",
        "credit_note"
      ],
      "type": "string"
    },
    "issue_date": {
      "description": "Date when the invoice was issued in DD/MM/YYYY format",
      "pattern": "^[0-3][0-9]/[0-1][0-9]/[0-9]{4}$",
      "type": "string"
    },
    "line_items": {
      "description": "Individual line items on the invoice",
      "items": {
        "properties": {
          "description": {
            "description": "Description of the product or service",
            "type": "string"
          },
          "line_total": {
            "description": "Total price for this line item in EUR",
            "type": "string"
          },
          "qty": {
            "description": "Quantity of items",
            "type": "string"
          },
          "unit_price": {
            "description": "Price per unit in EUR",
            "type": "string"
          }
        },
        "type": "object"
      },
      "type": "array"
    },
    "metadata": {
      "description": "Additional metadata about the extraction process",
      "type": "object"
    },
    "notes": {
      "description": "Additional notes or comments on the invoice",
      "type": "string"
    },
    "payment_terms": {
      "description": "Terms of payment (optional)",
      "type": "string"
    },
    "subtotal": {
      "description": "Subtotal amount before taxes",
      "pattern": "^[0-9]{1,3}(\\s?[0-9]{3})*(,[0-9]{2})?(\\s?\u20ac)?$",
      "type": "string"
    },
    "total_eur": {
      "description": "Total invoice amount in EUR currency",
      "pattern": "^[0-9]{1,3}(\\s?[0-9]{3})*(,[0-9]{2})?(\\s?\u20ac)?$",
      "type": "string"
    },
    "vat_amount": {
      "description": "VAT amount in EUR",
      "pattern": "^[0-9]{1,3}(\\s?[0-9]{3})*(,[0-9]{2})?(\\s?\u20ac)?$",
      "type": "string"
    },
    "vat_rate": {
      "description": "VAT percentage rate applied",
      "pattern": "^[0-9]{1,2}(,[0-9]{1,2})?%$",
      "type": "string"
    },
    "vendor_name": {
      "description": "Name of the company or person issuing the invoice",
      "type": "string"
    },
    "vendor_tax_id": {
      "description": "Tax identification number (NIF/CIF) of the vendor",
      "pattern": "^[A-Z0-9]\\d{7}[A-Z0-9]$",
      "type": "string"
    }
  },
  "required": [
    "invoice_number",
    "issue_date",
    "total_eur",
    "vat_rate",
    "vat_amount",
    "vendor_name",
    "vendor_tax_id",
    "buyer_name"
  ],
  "type": "object"
}
```

# Instructions
1. Extract all required fields and any available optional fields from the OCR text.
2. Normalize all extracted values to match the expected format in the schema.
3. For dates, ensure they are in DD/MM/YYYY format.
4. For currency amounts, keep the original format (with or without € symbol).
5. If you cannot find a required field, make your best guess and mark it with low confidence.
6. For line items, extract as many as you can identify.

<!--internal-->
# Analysis Process
1. First, identify the invoice structure and layout (header, items table, footer).
2. Look for key identifiers like "Factura", "Total", etc. to locate important sections.
3. Extract required fields first, then optional fields.
4. Validate data against the schema requirements.
5. Format the output as a valid JSON object.
<!--/internal-->

# Example Extractions

## Example 1

OCR Text:
```
EMPRESA EJEMPLO S.L.
C/ Ejemplo, 123
28001 Madrid, España
CIF: B12345678

FACTURA
Número: F2023-1234
Fecha: 15/06/2023

CLIENTE:
Cliente Ejemplo S.A.
C/ Cliente, 456
08001 Barcelona, España
CIF: A87654321

DESCRIPCIÓN          CANTIDAD    PRECIO     TOTAL
Servicio de consultoría      10     100,00 €   1000,00 €
Materiales de oficina         5      25,50 €    127,50 €
Soporte técnico              8      75,00 €    600,00 €

Base imponible:                             1727,50 €
IVA (21%):                                   362,78 €
TOTAL FACTURA:                              2090,28 €

Forma de pago: Transferencia bancaria
Vencimiento: 15/07/2023

Cuenta bancaria: ES12 3456 7890 1234 5678 9012
```

Correct Extraction:
```json
{
  "buyer_name": "Cliente Ejemplo S.A.",
  "buyer_tax_id": "A87654321",
  "invoice_number": "F2023-1234",
  "issue_date": "15/06/2023",
  "line_items": [
    {
      "description": "Servicio de consultor\u00eda",
      "line_total": "1000,00 \u20ac",
      "qty": "10",
      "unit_price": "100,00 \u20ac"
    },
    {
      "description": "Materiales de oficina",
      "line_total": "127,50 \u20ac",
      "qty": "5",
      "unit_price": "25,50 \u20ac"
    },
    {
      "description": "Soporte t\u00e9cnico",
      "line_total": "600,00 \u20ac",
      "qty": "8",
      "unit_price": "75,00 \u20ac"
    }
  ],
  "payment_terms": "Transferencia bancaria",
  "subtotal": "1727,50 \u20ac",
  "total_eur": "2090,28 \u20ac",
  "vat_amount": "362,78 \u20ac",
  "vat_rate": "21%",
  "vendor_name": "EMPRESA EJEMPLO S.L.",
  "vendor_tax_id": "B12345678"
}
```


## Example 2

OCR Text:
```
TECNOLOGÍA AVANZADA, S.A.
Avda. Innovación, 42
41092 Sevilla
NIF: A11223344

Factura Nº: TEC/2023/0089
Fecha de emisión: 22-03-2023

EMITIDO A:
Inversiones Futuras, S.L.
C/ Inversión, 78
28046 Madrid
NIF: B99887766

Concepto                      Unidades    P. unitario    Importe
---------------------------------------------------------------
Ordenador portátil HP Elite      2         899,00 €     1.798,00 €
Monitor 27" Dell UltraSharp     4         329,50 €     1.318,00 €
Servicio de instalación          1         250,00 €       250,00 €

Base imponible                                         3.366,00 €
IVA (21%)                                                706,86 €
TOTAL                                                  4.072,86 €

Condiciones de pago: 30 días mediante transferencia bancaria
Cuenta: ES98 7654 3210 9876 5432 1098
```

Correct Extraction:
```json
{
  "buyer_name": "Inversiones Futuras, S.L.",
  "buyer_tax_id": "B99887766",
  "invoice_number": "TEC/2023/0089",
  "issue_date": "22/03/2023",
  "line_items": [
    {
      "description": "Ordenador port\u00e1til HP Elite",
      "line_total": "1.798,00 \u20ac",
      "qty": "2",
      "unit_price": "899,00 \u20ac"
    },
    {
      "description": "Monitor 27\" Dell UltraSharp",
      "line_total": "1.318,00 \u20ac",
      "qty": "4",
      "unit_price": "329,50 \u20ac"
    },
    {
      "description": "Servicio de instalaci\u00f3n",
      "line_total": "250,00 \u20ac",
      "qty": "1",
      "unit_price": "250,00 \u20ac"
    }
  ],
  "payment_terms": "30 d\u00edas mediante transferencia bancaria",
  "subtotal": "3.366,00 \u20ac",
  "total_eur": "4.072,86 \u20ac",
  "vat_amount": "706,86 \u20ac",
  "vat_rate": "21%",
  "vendor_name": "TECNOLOG\u00cdA AVANZADA, S.A.",
  "vendor_tax_id": "A11223344"
}
```


## Example 3

OCR Text:
```
DISTRIBUCIONES MEDITERRÁNEAS, SL
Polígono Industrial Sur, Nave 15
46980 Valencia
CIF: B55667788

Cliente:
Hostelería Costa, SL
Avda. Playa, 123
03001 Alicante
CIF: B11335577

FACTURA Nº: DM-2023-0456
Fecha: 07/05/2023

Producto              Cant.   Precio/u    Total
-----------------------------------------
Aceite de oliva 5L      20     22,50      450,00
Vino tinto (caja 6)     15     32,00      480,00
Patatas (saco 25kg)     10     18,75      187,50

Subtotal:                             1.117,50
IVA 10%:                                111,75
TOTAL EUROS:                          1.229,25

Forma de pago: Recibo domiciliado
Vencimiento: 22/05/2023
```

Correct Extraction:
```json
{
  "buyer_name": "Hosteler\u00eda Costa, SL",
  "buyer_tax_id": "B11335577",
  "invoice_number": "DM-2023-0456",
  "issue_date": "07/05/2023",
  "line_items": [
    {
      "description": "Aceite de oliva 5L",
      "line_total": "450,00",
      "qty": "20",
      "unit_price": "22,50"
    },
    {
      "description": "Vino tinto (caja 6)",
      "line_total": "480,00",
      "qty": "15",
      "unit_price": "32,00"
    },
    {
      "description": "Patatas (saco 25kg)",
      "line_total": "187,50",
      "qty": "10",
      "unit_price": "18,75"
    }
  ],
  "payment_terms": "Recibo domiciliado",
  "subtotal": "1.117,50",
  "total_eur": "1.229,25",
  "vat_amount": "111,75",
  "vat_rate": "10%",
  "vendor_name": "DISTRIBUCIONES MEDITERR\u00c1NEAS, SL",
  "vendor_tax_id": "B55667788"
}
```



# Output Format
Respond ONLY with a valid JSON object containing all extracted fields, formatted according to the schema.
Do not include any explanations, notes, or additional text outside of the JSON object. 
```

### User Message
```
OCR Text:

Factura Pagado NO de referencia de pago 2suFZprY4TbarBvTOFSX Vendido por HONG KONG UGREEN LIMITED Fecha de la factura/Fecha de la entrega 28.04.2024 CARLOS LORENZO Número de la factura DS-ASE-INV-ES-2024-33264305 AVENIDA ISABEL DE VALOIS 90, BAJO A Total pendiente 69.99 € MADRID, MADRID, 28050 ES El IVA ha sido declarado Amazon Services Europe por S.a.r.L. IVA LU19647148 Si tienes preguntas sobre tus pedidos, visita https://www.amazon.es/contacto Dirección de facturación Dirección de envío Vendido por Carlos Lorenzo Carlos Lorenzo HONG KONG UGREEN LIMITED Avenida Isabel de Valois 90, Bajo A Avenida Isabel de Valois 90, Bajo A 19H WAN DI PLAZA Madrid, Madrid, 28050 Madrid, Madrid, 28050 3 TAI YU STREET, SAN PO KONG, KL ES ES HONG KONG, HONG KONG, 999077 HK Información del pedido Fecha del pedido 27.04.2024 Número del pedido 171-4544162-9429147 Detalles de la factura Descripción Cant. P. Unitario IVA % P. Unitario Precio total (IVA excluido) (IVA incluido) (IVA incluido) UGREEN Revodok Pro 210 Docking Station USB C 10 En 1 Doble HDMI 1 57,84 € 21% 69,99 € 69,99 € 8K30Hz 4K60Hz Hub Adaptador USB C a 2 HDMI Ethernet Gigabit USB 3.0 PD 100W Lector Tarjeta SD TF Compatible con MacBook Pro Air M2 M1 | BOBXDQS4BD Envío 0,00 € 0,00 € 0,00 € Total 69,99 € IVA % Precio total IVA (IVA excluido) 21% 57,84 € 12,15€ Total 57,84 € 12,15€
Factura Pagado NO de referencia de pago 2suFZprY4TbarBvTOFSX Vendido por Comfort Click Ltd Fecha de la factura/Fecha de la entrega 28.04.2024 CARLOS LORENZO Número de la factura DS-ASE-INV-ES-2024-33264321 AVENIDA ISABEL DE VALOIS 90, BAJO A Total pendiente 15,49 € MADRID, MADRID, 28050 ES El IVA ha sido declarado Amazon Services Europe por S.a.r.L. IVA LU19647148 Si tienes preguntas sobre tus pedidos, visita https://www.amazon.es/contacto Dirección de facturación Dirección de envío Vendido por Carlos Lorenzo Carlos Lorenzo Comfort Click Ltd Avenida Isabel de Valois 90, Bajo A Avenida Isabel de Valois 90, Bajo A 106 Lower Addiscombe Road Madrid, Madrid, 28050 Madrid, Madrid, 28050 CROYDON, Surrey, CRO 6AD ES ES GB Información del pedido Fecha del pedido 27.04.2024 Número del pedido 171-4544162-9429147 Detalles de la factura Descripción Cant. P. Unitario IVA % P. Unitario Precio total (IVA excluido) (IVA incluido) (IVA incluido) Vinagre de Sidra de Manzana con la Madre 1860mg de Potencia 180 1 14,08 € 10% 15,49 € 15,49 € Cápsulas Veganas - Con Probióticos, Cúrcuma, Jengibre y Pimienta de Cayena, Suplemento Dietético Natural Para 2 Meses | BO981NCGQPB Envío 0,00 € 0,00 € 0,00 € Total 15,49 € IVA % Precio total IVA (IVA excluido) 10% 14,08 € 1,41€ Total 14,08 € 1,41€

Initial fields extracted:

{
  "invoice_number": "1",
  "total_eur": "69,99",
  "vat_rate": "10%",
  "vat_amount": "1",
  "payment_terms": "2suFZprY4TbarBvTOFSX Vendido por HONG KONG UGREEN LIMITED Fecha de la factura/Fecha de la entrega 28.04.2024 CARLOS LORENZO Número de la factura DS - ASE - INV - ES - 2024 - 33264305 AVENIDA ISABEL DE VALOIS 90, BAJO A Total pendiente 69.99 € MADRID, MADRID, 28050 ES El IVA ha sido declarado Amazon Services Europe por S.a.r.L. IVA LU19647148 Si tienes preguntas sobre tus pedidos, visita https : //www.amazon.es/contacto Dirección de facturación Dirección de envío Vendido por Carlos Lorenzo Carlos Lorenzo HONG KONG UGREEN LIMITED Avenida Isabel de Valois 90, Bajo A Avenida Isabel de Valois 90, Bajo A 19H WAN DI PLAZA Madrid, Madrid, 28050 Madrid, Madrid, 28050 3 TAI YU STREET, SAN PO KONG, KL ES ES HONG KONG, HONG KONG, 999077 HK Información del pedido Fecha del pedido 27.04.2024 Número del pedido 171 - 4544162 - 9429147 Detalles de la factura Descripción Cant. P. Unitario IVA % P. Unitario Precio total (IVA excluido) (IVA incluido) (IVA incluido) UGREEN Revodok Pro 210 Docking Station USB C 10 En 1 Doble HDMI 1 57,84 € 21% 69,99 € 69,99 € 8K30Hz 4K60Hz Hub Adaptador USB C a 2 HDMI Ethernet Gigabit USB 3.0 PD 100W Lector Tarjeta SD TF Compatible con MacBook Pro Air M2 M1 | BOBXDQS4BD Envío 0,00 € 0,00 € 0,00 € Total 69,99 € IVA % Precio total IVA (IVA excluido) 21% 57,84 € 12,15€ Total 57,84 € 12,15€ Factura Pagado NO de referencia de pago 2suFZprY4TbarBvTOFSX Vendido por Comfort Click Ltd Fecha de la factura/Fecha de la entrega 28.04.2024 CARLOS LORENZO Número de la factura DS - ASE - INV - ES - 2024 - 33264321 AVENIDA ISABEL DE VALOIS 90, BAJO A Total pendiente 15,49 € MADRID, MADRID, 28050 ES El IVA ha sido declarado Amazon Services Europe por S.a.r.L. IVA LU19647148 Si tienes preguntas sobre tus pedidos, visita https : //www.amazon.es/contacto Dirección de facturación Dirección de envío Vendido por Carlos Lorenzo Carlos Lorenzo Comfort Click Ltd Avenida Isabel de Valois 90, Bajo A Avenida Isabel de Valois 90, Bajo A 106 Lower Addiscombe Road Madrid, Madrid, 28050 Madrid, Madrid, 28050 CROYDON, Surrey, CRO 6AD ES ES GB Información del pedido Fecha del pedido 27.04.2024 Número del pedido 171 - 4544162 - 9429147 Detalles de la factura Descripción Cant. P. Unitario IVA % P. Unitario Precio total (IVA excluido) (IVA incluido) (IVA incluido) Vinagre de Sidra de Manzana con la Madre 1860mg de Potencia 180 1 14,08 € 10% 15,49 € 15,49 € Cápsulas Veganas - Con Probióticos, Cúrcuma, Jengibre y Pimienta de Cayena, Suplemento Dietético Natural Para 2 Meses | BO981NCGQPB Envío 0,00 € 0,00 € 0,00 € Total 15,49 € IVA % Precio total IVA (IVA excluido) 10% 14,08 € 1,41€ Total 14,08 € 1,41€",
  "metadata": {
    "extraction_method": "regex_heuristics",
    "extraction_timestamp": "2025-05-08T15:18:48.827440"
  }
}
```

### Initial Fields
```json
{
  "invoice_number": "1",
  "total_eur": "69,99",
  "vat_rate": "10%",
  "vat_amount": "1",
  "payment_terms": "2suFZprY4TbarBvTOFSX Vendido por HONG KONG UGREEN LIMITED Fecha de la factura/Fecha de la entrega 28.04.2024 CARLOS LORENZO Número de la factura DS - ASE - INV - ES - 2024 - 33264305 AVENIDA ISABEL DE VALOIS 90, BAJO A Total pendiente 69.99 € MADRID, MADRID, 28050 ES El IVA ha sido declarado Amazon Services Europe por S.a.r.L. IVA LU19647148 Si tienes preguntas sobre tus pedidos, visita https : //www.amazon.es/contacto Dirección de facturación Dirección de envío Vendido por Carlos Lorenzo Carlos Lorenzo HONG KONG UGREEN LIMITED Avenida Isabel de Valois 90, Bajo A Avenida Isabel de Valois 90, Bajo A 19H WAN DI PLAZA Madrid, Madrid, 28050 Madrid, Madrid, 28050 3 TAI YU STREET, SAN PO KONG, KL ES ES HONG KONG, HONG KONG, 999077 HK Información del pedido Fecha del pedido 27.04.2024 Número del pedido 171 - 4544162 - 9429147 Detalles de la factura Descripción Cant. P. Unitario IVA % P. Unitario Precio total (IVA excluido) (IVA incluido) (IVA incluido) UGREEN Revodok Pro 210 Docking Station USB C 10 En 1 Doble HDMI 1 57,84 € 21% 69,99 € 69,99 € 8K30Hz 4K60Hz Hub Adaptador USB C a 2 HDMI Ethernet Gigabit USB 3.0 PD 100W Lector Tarjeta SD TF Compatible con MacBook Pro Air M2 M1 | BOBXDQS4BD Envío 0,00 € 0,00 € 0,00 € Total 69,99 € IVA % Precio total IVA (IVA excluido) 21% 57,84 € 12,15€ Total 57,84 € 12,15€ Factura Pagado NO de referencia de pago 2suFZprY4TbarBvTOFSX Vendido por Comfort Click Ltd Fecha de la factura/Fecha de la entrega 28.04.2024 CARLOS LORENZO Número de la factura DS - ASE - INV - ES - 2024 - 33264321 AVENIDA ISABEL DE VALOIS 90, BAJO A Total pendiente 15,49 € MADRID, MADRID, 28050 ES El IVA ha sido declarado Amazon Services Europe por S.a.r.L. IVA LU19647148 Si tienes preguntas sobre tus pedidos, visita https : //www.amazon.es/contacto Dirección de facturación Dirección de envío Vendido por Carlos Lorenzo Carlos Lorenzo Comfort Click Ltd Avenida Isabel de Valois 90, Bajo A Avenida Isabel de Valois 90, Bajo A 106 Lower Addiscombe Road Madrid, Madrid, 28050 Madrid, Madrid, 28050 CROYDON, Surrey, CRO 6AD ES ES GB Información del pedido Fecha del pedido 27.04.2024 Número del pedido 171 - 4544162 - 9429147 Detalles de la factura Descripción Cant. P. Unitario IVA % P. Unitario Precio total (IVA excluido) (IVA incluido) (IVA incluido) Vinagre de Sidra de Manzana con la Madre 1860mg de Potencia 180 1 14,08 € 10% 15,49 € 15,49 € Cápsulas Veganas - Con Probióticos, Cúrcuma, Jengibre y Pimienta de Cayena, Suplemento Dietético Natural Para 2 Meses | BO981NCGQPB Envío 0,00 € 0,00 € 0,00 € Total 15,49 € IVA % Precio total IVA (IVA excluido) 10% 14,08 € 1,41€ Total 14,08 € 1,41€",
  "metadata": {
    "extraction_method": "regex_heuristics",
    "extraction_timestamp": "2025-05-08T15:18:48.827440"
  }
}
```

---


## Prompt Log Entry - 2025-05-08 17:36:54

### System Message
```
You are a meticulous Spanish invoice parser. Your job is to extract structured data from invoice OCR text according to a specific schema.

# Schema
The extracted data must conform to this schema:
```json
{
  "properties": {
    "// 1. Header / Parties": {
      "description": "Document header and party information",
      "type": "null"
    },
    "// 2. Totals \u0026 Taxes": {
      "description": "Financial totals and tax information",
      "type": "null"
    },
    "// 3. Line Items": {
      "description": "Individual line items on the invoice",
      "type": "null"
    },
    "// 4. Payment Info": {
      "description": "Payment terms and banking information",
      "type": "null"
    },
    "// 5. Regulatory \u0026 Metadata": {
      "description": "Regulatory information and document metadata",
      "type": "null"
    },
    "// 6. System Metadata": {
      "description": "System processing metadata",
      "type": "null"
    },
    "aeat_event_codes": {
      "description": "AEAT (Spanish Tax Agency) event codes",
      "type": "array"
    },
    "bank_account": {
      "description": "Bank account number or IBAN",
      "pattern": "^[A-Z]{2}[0-9]{2}[A-Z0-9]{4}[0-9]{7}([A-Z0-9]?){0,16}$",
      "type": "string"
    },
    "buyer_address": {
      "description": "Address of the buyer (optional)",
      "type": "string"
    },
    "buyer_name": {
      "description": "Name of the company or person receiving the invoice",
      "type": "string"
    },
    "buyer_tax_id": {
      "description": "Tax identification number (NIF/VAT) of the buyer",
      "pattern": "^[A-Z0-9]\\d{7}[A-Z0-9]$",
      "type": "string"
    },
    "currency": {
      "description": "Currency code used in the invoice",
      "enum": [
        "EUR",
        "USD",
        "GBP"
      ],
      "type": "string"
    },
    "discount_amount": {
      "description": "Discount amount in currency",
      "pattern": "^[0-9]{1,3}(\\s?[0-9]{3})*(,[0-9]{2})?(\\s?\u20ac)?$",
      "type": "string"
    },
    "discount_rate": {
      "description": "Discount percentage rate applied",
      "pattern": "^[0-9]{1,2}(,[0-9]{1,2})?%$",
      "type": "string"
    },
    "due_date": {
      "description": "Payment due date in DD/MM/YYYY format",
      "pattern": "^[0-3][0-9]/[0-1][0-9]/[0-9]{4}$",
      "type": "string"
    },
    "electronic_signature": {
      "description": "Electronic signature validity information",
      "type": "string"
    },
    "igic_amount": {
      "description": "IGIC amount in currency",
      "pattern": "^[0-9]{1,3}(\\s?[0-9]{3})*(,[0-9]{2})?(\\s?\u20ac)?$",
      "type": "string"
    },
    "igic_rate": {
      "description": "IGIC (Canary Islands General Indirect Tax) rate",
      "pattern": "^[0-9]{1,2}(,[0-9]{1,2})?%$",
      "type": "string"
    },
    "invoice_number": {
      "description": "Invoice identification number (unique)",
      "type": "string"
    },
    "invoice_series": {
      "description": "Invoice series identifier",
      "type": "string"
    },
    "invoice_type": {
      "description": "Type of invoice document",
      "enum": [
        "invoice",
        "simplified",
        "rectification",
        "credit_note",
        "debit_note"
      ],
      "type": "string"
    },
    "irpf_amount": {
      "description": "IRPF amount in currency",
      "pattern": "^[0-9]{1,3}(\\s?[0-9]{3})*(,[0-9]{2})?(\\s?\u20ac)?$",
      "type": "string"
    },
    "irpf_rate": {
      "description": "IRPF (Personal Income Tax withholding) rate",
      "pattern": "^[0-9]{1,2}(,[0-9]{1,2})?%$",
      "type": "string"
    },
    "issue_date": {
      "description": "Date when the invoice was issued in DD/MM/YYYY format",
      "pattern": "^[0-3][0-9]/[0-1][0-9]/[0-9]{4}$",
      "type": "string"
    },
    "line_items": {
      "description": "Individual line items on the invoice",
      "items": {
        "properties": {
          "description": {
            "description": "Description of the product or service",
            "type": "string"
          },
          "line_discount_rate": {
            "description": "Discount percentage for this line",
            "type": "string"
          },
          "line_number": {
            "description": "Line item number or identifier",
            "type": "string"
          },
          "line_tax_amount": {
            "description": "Tax amount for this line",
            "type": "string"
          },
          "line_tax_rate": {
            "description": "Tax rate applied to this line",
            "type": "string"
          },
          "line_total": {
            "description": "Total price for this line item in currency",
            "type": "string"
          },
          "qty": {
            "description": "Quantity of items",
            "type": "string"
          },
          "unit_of_measure": {
            "description": "Unit of measure (e.g., units, kg, hours)",
            "type": "string"
          },
          "unit_price": {
            "description": "Price per unit in currency",
            "type": "string"
          }
        },
        "type": "object"
      },
      "type": "array"
    },
    "metadata": {
      "description": "Additional metadata about the extraction process",
      "type": "object"
    },
    "notes": {
      "description": "Additional notes or comments on the invoice",
      "type": "string"
    },
    "original_invoice_ref": {
      "description": "Reference to original invoice (if credit/debit note)",
      "type": "string"
    },
    "payment_method": {
      "description": "Method of payment (transfer, SEPA, card, etc.)",
      "enum": [
        "transfer",
        "sepa",
        "card",
        "cash",
        "check",
        "other"
      ],
      "type": "string"
    },
    "payment_terms": {
      "description": "Terms of payment (e.g., 30 days)",
      "type": "string"
    },
    "qr_code_hash": {
      "description": "QR code or CSV hash (Facturae)",
      "type": "string"
    },
    "sii_status": {
      "description": "SII submission status",
      "enum": [
        "pending",
        "submitted",
        "accepted",
        "rejected",
        "unknown"
      ],
      "type": "string"
    },
    "sii_submission_id": {
      "description": "SII (Immediate Information Supply) submission ID",
      "type": "string"
    },
    "surcharge_amount": {
      "description": "Surcharge amount in currency",
      "pattern": "^[0-9]{1,3}(\\s?[0-9]{3})*(,[0-9]{2})?(\\s?\u20ac)?$",
      "type": "string"
    },
    "surcharge_rate": {
      "description": "Surcharge of equivalence rate",
      "pattern": "^[0-9]{1,2}(,[0-9]{1,2})?%$",
      "type": "string"
    },
    "swift_bic": {
      "description": "SWIFT/BIC code of the bank",
      "pattern": "^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$",
      "type": "string"
    },
    "taxable_base": {
      "description": "Taxable base subtotal amount before taxes",
      "pattern": "^[0-9]{1,3}(\\s?[0-9]{3})*(,[0-9]{2})?(\\s?\u20ac)?$",
      "type": "string"
    },
    "total_amount": {
      "description": "Total amount payable (including all taxes)",
      "pattern": "^[0-9]{1,3}(\\s?[0-9]{3})*(,[0-9]{2})?(\\s?\u20ac)?$",
      "type": "string"
    },
    "total_gross": {
      "description": "Total gross amount (before taxes)",
      "pattern": "^[0-9]{1,3}(\\s?[0-9]{3})*(,[0-9]{2})?(\\s?\u20ac)?$",
      "type": "string"
    },
    "vat_amount": {
      "description": "VAT amount in currency",
      "pattern": "^[0-9]{1,3}(\\s?[0-9]{3})*(,[0-9]{2})?(\\s?\u20ac)?$",
      "type": "string"
    },
    "vat_breakdown": {
      "description": "Breakdown of multiple VAT rates and amounts if applicable",
      "type": "array"
    },
    "vat_rate": {
      "description": "VAT percentage rate applied",
      "pattern": "^[0-9]{1,2}(,[0-9]{1,2})?%$",
      "type": "string"
    },
    "vendor_address": {
      "description": "Fiscal address of the vendor",
      "type": "string"
    },
    "vendor_name": {
      "description": "Legal name of the company or person issuing the invoice",
      "type": "string"
    },
    "vendor_tax_id": {
      "description": "Tax identification number (NIF/CIF) of the vendor",
      "pattern": "^[A-Z0-9]\\d{7}[A-Z0-9]$",
      "type": "string"
    }
  },
  "required": [
    "invoice_number",
    "issue_date",
    "vendor_name",
    "vendor_tax_id",
    "vendor_address",
    "buyer_name",
    "buyer_tax_id",
    "taxable_base",
    "vat_rate",
    "vat_amount",
    "total_amount"
  ],
  "type": "object"
}
```

# Instructions
1. Extract all required fields and any available optional fields from the OCR text.
2. Normalize all extracted values to match the expected format in the schema.
3. For dates, ensure they are in DD/MM/YYYY format.
4. For currency amounts, keep the original format (with or without € symbol).
5. If you cannot find a required field, make your best guess and mark it with low confidence.
6. For line items, extract as many as you can identify with all available details.
7. If multiple VAT rates are present, include them in the vat_breakdown array.
8. For regulatory information (SII, AEAT codes, etc.), only include if explicitly present.

<!--internal-->
# Analysis Process
1. First, identify the invoice structure and layout (header, items table, footer).
2. Look for key identifiers like "Factura", "Total", "IVA", "NIF", "CIF", etc. to locate important sections.
3. Extract vendor and buyer details (names, tax IDs, addresses).
4. Identify and extract line items with all available details.
5. Extract financial totals, tax breakdowns, and payment information.
6. Note any regulatory details or special designations.
7. Format the output as a valid JSON object according to schema requirements.
<!--/internal-->

# Spanish Invoice Field Guide

1. Header/Parties:
   - Look for "Factura", "Número", "Serie" for invoice identifiers
   - Vendor details usually at the top with "Emisor", "Proveedor", or company letterhead
   - Look for "NIF:" or "CIF:" followed by tax IDs (format like B12345678)
   - Buyer details often have "Cliente", "Destinatario", or "Datos del cliente"
   
2. Totals & Taxes:
   - Base imponible = Taxable base (before VAT)
   - IVA = VAT (standard rates: 21%, 10%, 4%)
   - IGIC = Canary Islands tax (if applicable)
   - IRPF = Income tax withholding (often 15% for professionals)
   - Recargo de equivalencia = Surcharge of equivalence
   - Total = Final amount including all taxes
   
3. Line Items:
   - Usually in a table with descriptions, quantities, unit prices
   - May include article codes, reference numbers
   - Look for subtotals per line
   
4. Payment Details:
   - "Forma de pago" = Payment method
   - "Vencimiento" = Due date
   - Bank details often shown with "IBAN" or "Cuenta"
   - SWIFT/BIC codes may be present for international transfers
   
5. Regulatory Information:
   - Simplified invoices marked as "Factura Simplificada"
   - Credit notes marked as "Factura Rectificativa" or "Abono"
   - SII references if electronic reporting is used
   - QR codes may contain official verification information

# Example Extractions

## Example 1

OCR Text:
```
EMPRESA EJEMPLO S.L.
C/ Ejemplo, 123
28001 Madrid, España
CIF: B12345678

FACTURA
Número: F2023-1234
Fecha: 15/06/2023

CLIENTE:
Cliente Ejemplo S.A.
C/ Cliente, 456
08001 Barcelona, España
CIF: A87654321

DESCRIPCIÓN          CANTIDAD    PRECIO     TOTAL
Servicio de consultoría      10     100,00 €   1000,00 €
Materiales de oficina         5      25,50 €    127,50 €
Soporte técnico              8      75,00 €    600,00 €

Base imponible:                             1727,50 €
IVA (21%):                                   362,78 €
TOTAL FACTURA:                              2090,28 €

Forma de pago: Transferencia bancaria
Vencimiento: 15/07/2023

Cuenta bancaria: ES12 3456 7890 1234 5678 9012
```

Correct Extraction:
```json
{
  "buyer_name": "Cliente Ejemplo S.A.",
  "buyer_tax_id": "A87654321",
  "invoice_number": "F2023-1234",
  "issue_date": "15/06/2023",
  "line_items": [
    {
      "description": "Servicio de consultor\u00eda",
      "line_total": "1000,00 \u20ac",
      "qty": "10",
      "unit_price": "100,00 \u20ac"
    },
    {
      "description": "Materiales de oficina",
      "line_total": "127,50 \u20ac",
      "qty": "5",
      "unit_price": "25,50 \u20ac"
    },
    {
      "description": "Soporte t\u00e9cnico",
      "line_total": "600,00 \u20ac",
      "qty": "8",
      "unit_price": "75,00 \u20ac"
    }
  ],
  "payment_terms": "Transferencia bancaria",
  "subtotal": "1727,50 \u20ac",
  "total_eur": "2090,28 \u20ac",
  "vat_amount": "362,78 \u20ac",
  "vat_rate": "21%",
  "vendor_name": "EMPRESA EJEMPLO S.L.",
  "vendor_tax_id": "B12345678"
}
```


## Example 2

OCR Text:
```
TECNOLOGÍA AVANZADA, S.A.
Avda. Innovación, 42
41092 Sevilla
NIF: A11223344

Factura Nº: TEC/2023/0089
Fecha de emisión: 22-03-2023

EMITIDO A:
Inversiones Futuras, S.L.
C/ Inversión, 78
28046 Madrid
NIF: B99887766

Concepto                      Unidades    P. unitario    Importe
---------------------------------------------------------------
Ordenador portátil HP Elite      2         899,00 €     1.798,00 €
Monitor 27" Dell UltraSharp     4         329,50 €     1.318,00 €
Servicio de instalación          1         250,00 €       250,00 €

Base imponible                                         3.366,00 €
IVA (21%)                                                706,86 €
TOTAL                                                  4.072,86 €

Condiciones de pago: 30 días mediante transferencia bancaria
Cuenta: ES98 7654 3210 9876 5432 1098
```

Correct Extraction:
```json
{
  "buyer_name": "Inversiones Futuras, S.L.",
  "buyer_tax_id": "B99887766",
  "invoice_number": "TEC/2023/0089",
  "issue_date": "22/03/2023",
  "line_items": [
    {
      "description": "Ordenador port\u00e1til HP Elite",
      "line_total": "1.798,00 \u20ac",
      "qty": "2",
      "unit_price": "899,00 \u20ac"
    },
    {
      "description": "Monitor 27\" Dell UltraSharp",
      "line_total": "1.318,00 \u20ac",
      "qty": "4",
      "unit_price": "329,50 \u20ac"
    },
    {
      "description": "Servicio de instalaci\u00f3n",
      "line_total": "250,00 \u20ac",
      "qty": "1",
      "unit_price": "250,00 \u20ac"
    }
  ],
  "payment_terms": "30 d\u00edas mediante transferencia bancaria",
  "subtotal": "3.366,00 \u20ac",
  "total_eur": "4.072,86 \u20ac",
  "vat_amount": "706,86 \u20ac",
  "vat_rate": "21%",
  "vendor_name": "TECNOLOG\u00cdA AVANZADA, S.A.",
  "vendor_tax_id": "A11223344"
}
```


## Example 3

OCR Text:
```
DISTRIBUCIONES MEDITERRÁNEAS, SL
Polígono Industrial Sur, Nave 15
46980 Valencia
CIF: B55667788

Cliente:
Hostelería Costa, SL
Avda. Playa, 123
03001 Alicante
CIF: B11335577

FACTURA Nº: DM-2023-0456
Fecha: 07/05/2023

Producto              Cant.   Precio/u    Total
-----------------------------------------
Aceite de oliva 5L      20     22,50      450,00
Vino tinto (caja 6)     15     32,00      480,00
Patatas (saco 25kg)     10     18,75      187,50

Subtotal:                             1.117,50
IVA 10%:                                111,75
TOTAL EUROS:                          1.229,25

Forma de pago: Recibo domiciliado
Vencimiento: 22/05/2023
```

Correct Extraction:
```json
{
  "buyer_name": "Hosteler\u00eda Costa, SL",
  "buyer_tax_id": "B11335577",
  "invoice_number": "DM-2023-0456",
  "issue_date": "07/05/2023",
  "line_items": [
    {
      "description": "Aceite de oliva 5L",
      "line_total": "450,00",
      "qty": "20",
      "unit_price": "22,50"
    },
    {
      "description": "Vino tinto (caja 6)",
      "line_total": "480,00",
      "qty": "15",
      "unit_price": "32,00"
    },
    {
      "description": "Patatas (saco 25kg)",
      "line_total": "187,50",
      "qty": "10",
      "unit_price": "18,75"
    }
  ],
  "payment_terms": "Recibo domiciliado",
  "subtotal": "1.117,50",
  "total_eur": "1.229,25",
  "vat_amount": "111,75",
  "vat_rate": "10%",
  "vendor_name": "DISTRIBUCIONES MEDITERR\u00c1NEAS, SL",
  "vendor_tax_id": "B55667788"
}
```



# Output Format
Respond ONLY with a valid JSON object containing all extracted fields, formatted according to the schema.
Do not include any explanations, notes, or additional text outside of the JSON object. 
```

### User Message
```
OCR Text:

Factura Pagado NO de referencia de pago 2suFZprY4TbarBvTOFSX Vendido por HONG KONG UGREEN LIMITED Fecha de la factura/Fecha de la entrega 28.04.2024 CARLOS LORENZO Número de la factura DS-ASE-INV-ES-2024-33264305 AVENIDA ISABEL DE VALOIS 90, BAJO A Total pendiente 69.99 € MADRID, MADRID, 28050 ES El IVA ha sido declarado Amazon Services Europe por S.a.r.L. IVA LU19647148 Si tienes preguntas sobre tus pedidos, visita https://www.amazon.es/contacto Dirección de facturación Dirección de envío Vendido por Carlos Lorenzo Carlos Lorenzo HONG KONG UGREEN LIMITED Avenida Isabel de Valois 90, Bajo A Avenida Isabel de Valois 90, Bajo A 19H WAN DI PLAZA Madrid, Madrid, 28050 Madrid, Madrid, 28050 3 TAI YU STREET, SAN PO KONG, KL ES ES HONG KONG, HONG KONG, 999077 HK Información del pedido Fecha del pedido 27.04.2024 Número del pedido 171-4544162-9429147 Detalles de la factura Descripción Cant. P. Unitario IVA % P. Unitario Precio total (IVA excluido) (IVA incluido) (IVA incluido) UGREEN Revodok Pro 210 Docking Station USB C 10 En 1 Doble HDMI 1 57,84 € 21% 69,99 € 69,99 € 8K30Hz 4K60Hz Hub Adaptador USB C a 2 HDMI Ethernet Gigabit USB 3.0 PD 100W Lector Tarjeta SD TF Compatible con MacBook Pro Air M2 M1 | BOBXDQS4BD Envío 0,00 € 0,00 € 0,00 € Total 69,99 € IVA % Precio total IVA (IVA excluido) 21% 57,84 € 12,15€ Total 57,84 € 12,15€
Factura Pagado NO de referencia de pago 2suFZprY4TbarBvTOFSX Vendido por Comfort Click Ltd Fecha de la factura/Fecha de la entrega 28.04.2024 CARLOS LORENZO Número de la factura DS-ASE-INV-ES-2024-33264321 AVENIDA ISABEL DE VALOIS 90, BAJO A Total pendiente 15,49 € MADRID, MADRID, 28050 ES El IVA ha sido declarado Amazon Services Europe por S.a.r.L. IVA LU19647148 Si tienes preguntas sobre tus pedidos, visita https://www.amazon.es/contacto Dirección de facturación Dirección de envío Vendido por Carlos Lorenzo Carlos Lorenzo Comfort Click Ltd Avenida Isabel de Valois 90, Bajo A Avenida Isabel de Valois 90, Bajo A 106 Lower Addiscombe Road Madrid, Madrid, 28050 Madrid, Madrid, 28050 CROYDON, Surrey, CRO 6AD ES ES GB Información del pedido Fecha del pedido 27.04.2024 Número del pedido 171-4544162-9429147 Detalles de la factura Descripción Cant. P. Unitario IVA % P. Unitario Precio total (IVA excluido) (IVA incluido) (IVA incluido) Vinagre de Sidra de Manzana con la Madre 1860mg de Potencia 180 1 14,08 € 10% 15,49 € 15,49 € Cápsulas Veganas - Con Probióticos, Cúrcuma, Jengibre y Pimienta de Cayena, Suplemento Dietético Natural Para 2 Meses | BO981NCGQPB Envío 0,00 € 0,00 € 0,00 € Total 15,49 € IVA % Precio total IVA (IVA excluido) 10% 14,08 € 1,41€ Total 14,08 € 1,41€

Initial fields extracted:

{
  "invoice_number": "1",
  "total_eur": "69,99",
  "vat_rate": "10%",
  "vat_amount": "1",
  "payment_terms": "2suFZprY4TbarBvTOFSX Vendido por HONG KONG UGREEN LIMITED Fecha de la factura/Fecha de la entrega 28.04.2024 CARLOS LORENZO Número de la factura DS - ASE - INV - ES - 2024 - 33264305 AVENIDA ISABEL DE VALOIS 90, BAJO A Total pendiente 69.99 € MADRID, MADRID, 28050 ES El IVA ha sido declarado Amazon Services Europe por S.a.r.L. IVA LU19647148 Si tienes preguntas sobre tus pedidos, visita https : //www.amazon.es/contacto Dirección de facturación Dirección de envío Vendido por Carlos Lorenzo Carlos Lorenzo HONG KONG UGREEN LIMITED Avenida Isabel de Valois 90, Bajo A Avenida Isabel de Valois 90, Bajo A 19H WAN DI PLAZA Madrid, Madrid, 28050 Madrid, Madrid, 28050 3 TAI YU STREET, SAN PO KONG, KL ES ES HONG KONG, HONG KONG, 999077 HK Información del pedido Fecha del pedido 27.04.2024 Número del pedido 171 - 4544162 - 9429147 Detalles de la factura Descripción Cant. P. Unitario IVA % P. Unitario Precio total (IVA excluido) (IVA incluido) (IVA incluido) UGREEN Revodok Pro 210 Docking Station USB C 10 En 1 Doble HDMI 1 57,84 € 21% 69,99 € 69,99 € 8K30Hz 4K60Hz Hub Adaptador USB C a 2 HDMI Ethernet Gigabit USB 3.0 PD 100W Lector Tarjeta SD TF Compatible con MacBook Pro Air M2 M1 | BOBXDQS4BD Envío 0,00 € 0,00 € 0,00 € Total 69,99 € IVA % Precio total IVA (IVA excluido) 21% 57,84 € 12,15€ Total 57,84 € 12,15€ Factura Pagado NO de referencia de pago 2suFZprY4TbarBvTOFSX Vendido por Comfort Click Ltd Fecha de la factura/Fecha de la entrega 28.04.2024 CARLOS LORENZO Número de la factura DS - ASE - INV - ES - 2024 - 33264321 AVENIDA ISABEL DE VALOIS 90, BAJO A Total pendiente 15,49 € MADRID, MADRID, 28050 ES El IVA ha sido declarado Amazon Services Europe por S.a.r.L. IVA LU19647148 Si tienes preguntas sobre tus pedidos, visita https : //www.amazon.es/contacto Dirección de facturación Dirección de envío Vendido por Carlos Lorenzo Carlos Lorenzo Comfort Click Ltd Avenida Isabel de Valois 90, Bajo A Avenida Isabel de Valois 90, Bajo A 106 Lower Addiscombe Road Madrid, Madrid, 28050 Madrid, Madrid, 28050 CROYDON, Surrey, CRO 6AD ES ES GB Información del pedido Fecha del pedido 27.04.2024 Número del pedido 171 - 4544162 - 9429147 Detalles de la factura Descripción Cant. P. Unitario IVA % P. Unitario Precio total (IVA excluido) (IVA incluido) (IVA incluido) Vinagre de Sidra de Manzana con la Madre 1860mg de Potencia 180 1 14,08 € 10% 15,49 € 15,49 € Cápsulas Veganas - Con Probióticos, Cúrcuma, Jengibre y Pimienta de Cayena, Suplemento Dietético Natural Para 2 Meses | BO981NCGQPB Envío 0,00 € 0,00 € 0,00 € Total 15,49 € IVA % Precio total IVA (IVA excluido) 10% 14,08 € 1,41€ Total 14,08 € 1,41€",
  "metadata": {
    "extraction_method": "regex_heuristics",
    "extraction_timestamp": "2025-05-08T17:36:54.450624"
  }
}
```

### Initial Fields
```json
{
  "invoice_number": "1",
  "total_eur": "69,99",
  "vat_rate": "10%",
  "vat_amount": "1",
  "payment_terms": "2suFZprY4TbarBvTOFSX Vendido por HONG KONG UGREEN LIMITED Fecha de la factura/Fecha de la entrega 28.04.2024 CARLOS LORENZO Número de la factura DS - ASE - INV - ES - 2024 - 33264305 AVENIDA ISABEL DE VALOIS 90, BAJO A Total pendiente 69.99 € MADRID, MADRID, 28050 ES El IVA ha sido declarado Amazon Services Europe por S.a.r.L. IVA LU19647148 Si tienes preguntas sobre tus pedidos, visita https : //www.amazon.es/contacto Dirección de facturación Dirección de envío Vendido por Carlos Lorenzo Carlos Lorenzo HONG KONG UGREEN LIMITED Avenida Isabel de Valois 90, Bajo A Avenida Isabel de Valois 90, Bajo A 19H WAN DI PLAZA Madrid, Madrid, 28050 Madrid, Madrid, 28050 3 TAI YU STREET, SAN PO KONG, KL ES ES HONG KONG, HONG KONG, 999077 HK Información del pedido Fecha del pedido 27.04.2024 Número del pedido 171 - 4544162 - 9429147 Detalles de la factura Descripción Cant. P. Unitario IVA % P. Unitario Precio total (IVA excluido) (IVA incluido) (IVA incluido) UGREEN Revodok Pro 210 Docking Station USB C 10 En 1 Doble HDMI 1 57,84 € 21% 69,99 € 69,99 € 8K30Hz 4K60Hz Hub Adaptador USB C a 2 HDMI Ethernet Gigabit USB 3.0 PD 100W Lector Tarjeta SD TF Compatible con MacBook Pro Air M2 M1 | BOBXDQS4BD Envío 0,00 € 0,00 € 0,00 € Total 69,99 € IVA % Precio total IVA (IVA excluido) 21% 57,84 € 12,15€ Total 57,84 € 12,15€ Factura Pagado NO de referencia de pago 2suFZprY4TbarBvTOFSX Vendido por Comfort Click Ltd Fecha de la factura/Fecha de la entrega 28.04.2024 CARLOS LORENZO Número de la factura DS - ASE - INV - ES - 2024 - 33264321 AVENIDA ISABEL DE VALOIS 90, BAJO A Total pendiente 15,49 € MADRID, MADRID, 28050 ES El IVA ha sido declarado Amazon Services Europe por S.a.r.L. IVA LU19647148 Si tienes preguntas sobre tus pedidos, visita https : //www.amazon.es/contacto Dirección de facturación Dirección de envío Vendido por Carlos Lorenzo Carlos Lorenzo Comfort Click Ltd Avenida Isabel de Valois 90, Bajo A Avenida Isabel de Valois 90, Bajo A 106 Lower Addiscombe Road Madrid, Madrid, 28050 Madrid, Madrid, 28050 CROYDON, Surrey, CRO 6AD ES ES GB Información del pedido Fecha del pedido 27.04.2024 Número del pedido 171 - 4544162 - 9429147 Detalles de la factura Descripción Cant. P. Unitario IVA % P. Unitario Precio total (IVA excluido) (IVA incluido) (IVA incluido) Vinagre de Sidra de Manzana con la Madre 1860mg de Potencia 180 1 14,08 € 10% 15,49 € 15,49 € Cápsulas Veganas - Con Probióticos, Cúrcuma, Jengibre y Pimienta de Cayena, Suplemento Dietético Natural Para 2 Meses | BO981NCGQPB Envío 0,00 € 0,00 € 0,00 € Total 15,49 € IVA % Precio total IVA (IVA excluido) 10% 14,08 € 1,41€ Total 14,08 € 1,41€",
  "metadata": {
    "extraction_method": "regex_heuristics",
    "extraction_timestamp": "2025-05-08T17:36:54.450624"
  }
}
```

---


## Prompt Log Entry - 2025-05-12 18:48:43

### System Message
```
You are a meticulous Spanish invoice parser. Your job is to extract structured data from invoice OCR text according to a specific schema.

# Schema
The extracted data must conform to this schema:
```json
{
  "properties": {
    "// 1. Header / Parties": {
      "description": "Document header and party information",
      "type": "null"
    },
    "// 2. Totals \u0026 Taxes": {
      "description": "Financial totals and tax information",
      "type": "null"
    },
    "// 3. Line Items": {
      "description": "Individual line items on the invoice",
      "type": "null"
    },
    "// 4. Payment Info": {
      "description": "Payment terms and banking information",
      "type": "null"
    },
    "// 5. Regulatory \u0026 Metadata": {
      "description": "Regulatory information and document metadata",
      "type": "null"
    },
    "// 6. System Metadata": {
      "description": "System processing metadata",
      "type": "null"
    },
    "aeat_event_codes": {
      "description": "AEAT (Spanish Tax Agency) event codes",
      "type": "array"
    },
    "bank_account": {
      "description": "Bank account number or IBAN",
      "pattern": "^[A-Z]{2}[0-9]{2}[A-Z0-9]{4}[0-9]{7}([A-Z0-9]?){0,16}$",
      "type": "string"
    },
    "buyer_address": {
      "description": "Address of the buyer (optional)",
      "type": "string"
    },
    "buyer_name": {
      "description": "Name of the company or person receiving the invoice",
      "type": "string"
    },
    "buyer_tax_id": {
      "description": "Tax identification number (NIF/VAT) of the buyer",
      "pattern": "^[A-Z0-9]\\d{7}[A-Z0-9]$",
      "type": "string"
    },
    "currency": {
      "description": "Currency code used in the invoice",
      "enum": [
        "EUR",
        "USD",
        "GBP"
      ],
      "type": "string"
    },
    "discount_amount": {
      "description": "Discount amount in currency",
      "pattern": "^[0-9]{1,3}(\\s?[0-9]{3})*(,[0-9]{2})?(\\s?\u20ac)?$",
      "type": "string"
    },
    "discount_rate": {
      "description": "Discount percentage rate applied",
      "pattern": "^[0-9]{1,2}(,[0-9]{1,2})?%$",
      "type": "string"
    },
    "due_date": {
      "description": "Payment due date in DD/MM/YYYY format",
      "pattern": "^[0-3][0-9]/[0-1][0-9]/[0-9]{4}$",
      "type": "string"
    },
    "electronic_signature": {
      "description": "Electronic signature validity information",
      "type": "string"
    },
    "igic_amount": {
      "description": "IGIC amount in currency",
      "pattern": "^[0-9]{1,3}(\\s?[0-9]{3})*(,[0-9]{2})?(\\s?\u20ac)?$",
      "type": "string"
    },
    "igic_rate": {
      "description": "IGIC (Canary Islands General Indirect Tax) rate",
      "pattern": "^[0-9]{1,2}(,[0-9]{1,2})?%$",
      "type": "string"
    },
    "invoice_number": {
      "description": "Invoice identification number (unique)",
      "type": "string"
    },
    "invoice_series": {
      "description": "Invoice series identifier",
      "type": "string"
    },
    "invoice_type": {
      "description": "Type of invoice document",
      "enum": [
        "invoice",
        "simplified",
        "rectification",
        "credit_note",
        "debit_note"
      ],
      "type": "string"
    },
    "irpf_amount": {
      "description": "IRPF amount in currency",
      "pattern": "^[0-9]{1,3}(\\s?[0-9]{3})*(,[0-9]{2})?(\\s?\u20ac)?$",
      "type": "string"
    },
    "irpf_rate": {
      "description": "IRPF (Personal Income Tax withholding) rate",
      "pattern": "^[0-9]{1,2}(,[0-9]{1,2})?%$",
      "type": "string"
    },
    "issue_date": {
      "description": "Date when the invoice was issued in DD/MM/YYYY format",
      "pattern": "^[0-3][0-9]/[0-1][0-9]/[0-9]{4}$",
      "type": "string"
    },
    "line_items": {
      "description": "Individual line items on the invoice",
      "items": {
        "properties": {
          "description": {
            "description": "Description of the product or service",
            "type": "string"
          },
          "line_discount_rate": {
            "description": "Discount percentage for this line",
            "type": "string"
          },
          "line_number": {
            "description": "Line item number or identifier",
            "type": "string"
          },
          "line_tax_amount": {
            "description": "Tax amount for this line",
            "type": "string"
          },
          "line_tax_rate": {
            "description": "Tax rate applied to this line",
            "type": "string"
          },
          "line_total": {
            "description": "Total price for this line item in currency",
            "type": "string"
          },
          "qty": {
            "description": "Quantity of items",
            "type": "string"
          },
          "unit_of_measure": {
            "description": "Unit of measure (e.g., units, kg, hours)",
            "type": "string"
          },
          "unit_price": {
            "description": "Price per unit in currency",
            "type": "string"
          }
        },
        "type": "object"
      },
      "type": "array"
    },
    "metadata": {
      "description": "Additional metadata about the extraction process",
      "type": "object"
    },
    "notes": {
      "description": "Additional notes or comments on the invoice",
      "type": "string"
    },
    "original_invoice_ref": {
      "description": "Reference to original invoice (if credit/debit note)",
      "type": "string"
    },
    "payment_method": {
      "description": "Method of payment (transfer, SEPA, card, etc.)",
      "enum": [
        "transfer",
        "sepa",
        "card",
        "cash",
        "check",
        "other"
      ],
      "type": "string"
    },
    "payment_terms": {
      "description": "Terms of payment (e.g., 30 days)",
      "type": "string"
    },
    "qr_code_hash": {
      "description": "QR code or CSV hash (Facturae)",
      "type": "string"
    },
    "sii_status": {
      "description": "SII submission status",
      "enum": [
        "pending",
        "submitted",
        "accepted",
        "rejected",
        "unknown"
      ],
      "type": "string"
    },
    "sii_submission_id": {
      "description": "SII (Immediate Information Supply) submission ID",
      "type": "string"
    },
    "surcharge_amount": {
      "description": "Surcharge amount in currency",
      "pattern": "^[0-9]{1,3}(\\s?[0-9]{3})*(,[0-9]{2})?(\\s?\u20ac)?$",
      "type": "string"
    },
    "surcharge_rate": {
      "description": "Surcharge of equivalence rate",
      "pattern": "^[0-9]{1,2}(,[0-9]{1,2})?%$",
      "type": "string"
    },
    "swift_bic": {
      "description": "SWIFT/BIC code of the bank",
      "pattern": "^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$",
      "type": "string"
    },
    "taxable_base": {
      "description": "Taxable base subtotal amount before taxes",
      "pattern": "^[0-9]{1,3}(\\s?[0-9]{3})*(,[0-9]{2})?(\\s?\u20ac)?$",
      "type": "string"
    },
    "total_amount": {
      "description": "Total amount payable (including all taxes)",
      "pattern": "^[0-9]{1,3}(\\s?[0-9]{3})*(,[0-9]{2})?(\\s?\u20ac)?$",
      "type": "string"
    },
    "total_gross": {
      "description": "Total gross amount (before taxes)",
      "pattern": "^[0-9]{1,3}(\\s?[0-9]{3})*(,[0-9]{2})?(\\s?\u20ac)?$",
      "type": "string"
    },
    "vat_amount": {
      "description": "VAT amount in currency",
      "pattern": "^[0-9]{1,3}(\\s?[0-9]{3})*(,[0-9]{2})?(\\s?\u20ac)?$",
      "type": "string"
    },
    "vat_breakdown": {
      "description": "Breakdown of multiple VAT rates and amounts if applicable",
      "type": "array"
    },
    "vat_rate": {
      "description": "VAT percentage rate applied",
      "pattern": "^[0-9]{1,2}(,[0-9]{1,2})?%$",
      "type": "string"
    },
    "vendor_address": {
      "description": "Fiscal address of the vendor",
      "type": "string"
    },
    "vendor_name": {
      "description": "Legal name of the company or person issuing the invoice",
      "type": "string"
    },
    "vendor_tax_id": {
      "description": "Tax identification number (NIF/CIF) of the vendor",
      "pattern": "^[A-Z0-9]\\d{7}[A-Z0-9]$",
      "type": "string"
    }
  },
  "required": [
    "invoice_number",
    "issue_date",
    "vendor_name",
    "vendor_tax_id",
    "vendor_address",
    "buyer_name",
    "buyer_tax_id",
    "taxable_base",
    "vat_rate",
    "vat_amount",
    "total_amount"
  ],
  "type": "object"
}
```

# Instructions
1. Extract all required fields and any available optional fields from the OCR text.
2. Use the following standardized formats:
   - Dates in ISO 8601 format (YYYY-MM-DD)
   - Numerical values for quantities, prices, and amounts
   - Percentage values for rates with % symbol (e.g., "21%")
   - Separate currency from amounts (use "currency": "EUR" field)
   - Group related fields in nested objects (vendor, buyer, payment_terms, etc.)
3. Use appropriate data types:
   - Numbers for amounts, quantities, rates (no string formatting)
   - Strings for identifiers, names, and text fields
   - Objects for structured data like addresses and payment details
4. Group vendor and buyer information into nested objects with name, tax_id, and address fields
5. Break down addresses into components when possible (street, postal_code, city, etc.)
6. Include item_type (product/service) for each line item
7. Create structured payment_terms with method, days, and due_date when available
8. Format bank account details as a structured object with iban and swift fields

<!--internal-->
# Analysis Process
1. First, identify the invoice structure and layout (header, items table, footer).
2. Look for key identifiers like "Factura", "Total", "IVA", "NIF", "CIF", etc. to locate important sections.
3. Extract vendor and buyer details into structured objects with nested address information.
4. Identify and extract line items with all available details including item type.
5. Extract financial totals as numeric values and separate the currency.
6. Format dates in ISO 8601 (YYYY-MM-DD) format.
7. Create structured payment and bank information.
8. Format the output as a valid JSON object according to schema requirements.
<!--/internal-->

# Spanish Invoice Field Guide

1. Header/Parties (convert to structured objects):
   - Look for "Factura", "Número", "Serie" for invoice identifiers
   - Vendor details usually at the top with "Emisor", "Proveedor", or company letterhead
   - Look for "NIF:" or "CIF:" followed by tax IDs (format like B12345678)
   - Buyer details often have "Cliente", "Destinatario", or "Datos del cliente"
   - Extract address components (street, number, postal code, city, etc.) when possible
   
2. Totals & Taxes (convert to numeric values):
   - Base imponible = Taxable base (before VAT)
   - IVA = VAT (standard rates: 21%, 10%, 4%) - keep as string with % symbol
   - IGIC = Canary Islands tax (if applicable)
   - IRPF = Income tax withholding (often 15% for professionals)
   - Recargo de equivalencia = Surcharge of equivalence
   - Total = Final amount including all taxes
   - Always separate currency from amounts
   
3. Line Items (use numeric values):
   - Usually in a table with descriptions, quantities, unit prices
   - May include article codes, reference numbers
   - Look for subtotals per line
   - Determine if each item is a product or service
   - Include currency for each line item
   
4. Payment Details (create structured object):
   - "Forma de pago" = Payment method
   - "Vencimiento" = Due date (convert to ISO format)
   - Bank details structured with IBAN and SWIFT fields
   - Payment terms with method, days, and due date when available
   
5. Regulatory Information:
   - Simplified invoices marked as "Factura Simplificada"
   - Credit notes marked as "Factura Rectificativa" or "Abono"
   - SII references if electronic reporting is used
   - QR codes may contain official verification information

# Example Extractions

## Example 1

OCR Text:
```
EMPRESA EJEMPLO S.L.
C/ Ejemplo, 123
28001 Madrid, España
CIF: B12345678

FACTURA
Número: F2023-1234
Fecha: 15/06/2023

CLIENTE:
Cliente Ejemplo S.A.
C/ Cliente, 456
08001 Barcelona, España
CIF: A87654321

DESCRIPCIÓN          CANTIDAD    PRECIO     TOTAL
Servicio de consultoría      10     100,00 €   1000,00 €
Materiales de oficina         5      25,50 €    127,50 €
Soporte técnico              8      75,00 €    600,00 €

Base imponible:                             1727,50 €
IVA (21%):                                   362,78 €
TOTAL FACTURA:                              2090,28 €

Forma de pago: Transferencia bancaria
Vencimiento: 15/07/2023

Cuenta bancaria: ES12 3456 7890 1234 5678 9012
```

Correct Extraction:
```json
{
  "bank_account": {
    "iban": "ES12 3456 7890 1234 5678 9012"
  },
  "buyer": {
    "address": {
      "city": "Barcelona",
      "country": "ES",
      "postal_code": "08001",
      "street_name": "Cliente",
      "street_number": "456",
      "street_type": "C/"
    },
    "name": "Cliente Ejemplo S.A.",
    "tax_id": "A87654321"
  },
  "currency": "EUR",
  "invoice_number": "F2023-1234",
  "issue_date": "2023-06-15",
  "line_items": [
    {
      "currency": "EUR",
      "description": "Servicio de consultor\u00eda",
      "item_type": "service",
      "line_total": 1000.0,
      "qty": 10,
      "unit_price": 100.0
    },
    {
      "currency": "EUR",
      "description": "Materiales de oficina",
      "item_type": "product",
      "line_total": 127.5,
      "qty": 5,
      "unit_price": 25.5
    },
    {
      "currency": "EUR",
      "description": "Soporte t\u00e9cnico",
      "item_type": "service",
      "line_total": 600.0,
      "qty": 8,
      "unit_price": 75.0
    }
  ],
  "payment_terms": {
    "due_date": "2023-07-15",
    "method": "transferencia"
  },
  "taxable_base": 1727.5,
  "total_amount": 2090.28,
  "vat_amount": 362.78,
  "vat_rate": "21%",
  "vendor": {
    "address": {
      "city": "Madrid",
      "country": "ES",
      "postal_code": "28001",
      "street_name": "Ejemplo",
      "street_number": "123",
      "street_type": "C/"
    },
    "name": "EMPRESA EJEMPLO S.L.",
    "tax_id": "B12345678"
  }
}
```


## Example 2

OCR Text:
```
TECNOLOGÍA AVANZADA, S.A.
Avda. Innovación, 42
41092 Sevilla
NIF: A11223344

Factura Nº: TEC/2023/0089
Fecha de emisión: 22-03-2023

EMITIDO A:
Inversiones Futuras, S.L.
C/ Inversión, 78
28046 Madrid
NIF: B99887766

Concepto                      Unidades    P. unitario    Importe
---------------------------------------------------------------
Ordenador portátil HP Elite      2         899,00 €     1.798,00 €
Monitor 27" Dell UltraSharp     4         329,50 €     1.318,00 €
Servicio de instalación          1         250,00 €       250,00 €

Base imponible                                         3.366,00 €
IVA (21%)                                                706,86 €
TOTAL                                                  4.072,86 €

Condiciones de pago: 30 días mediante transferencia bancaria
Cuenta: ES98 7654 3210 9876 5432 1098
```

Correct Extraction:
```json
{
  "bank_account": {
    "iban": "ES98 7654 3210 9876 5432 1098"
  },
  "buyer": {
    "address": {
      "city": "Madrid",
      "country": "ES",
      "postal_code": "28046",
      "street_name": "Inversi\u00f3n",
      "street_number": "78",
      "street_type": "C/"
    },
    "name": "Inversiones Futuras, S.L.",
    "tax_id": "B99887766"
  },
  "currency": "EUR",
  "invoice_number": "TEC/2023/0089",
  "issue_date": "2023-03-22",
  "line_items": [
    {
      "currency": "EUR",
      "description": "Ordenador port\u00e1til HP Elite",
      "item_type": "product",
      "line_total": 1798.0,
      "qty": 2,
      "unit_price": 899.0
    },
    {
      "currency": "EUR",
      "description": "Monitor 27\" Dell UltraSharp",
      "item_type": "product",
      "line_total": 1318.0,
      "qty": 4,
      "unit_price": 329.5
    },
    {
      "currency": "EUR",
      "description": "Servicio de instalaci\u00f3n",
      "item_type": "service",
      "line_total": 250.0,
      "qty": 1,
      "unit_price": 250.0
    }
  ],
  "payment_terms": {
    "days": 30,
    "method": "transferencia"
  },
  "taxable_base": 3366.0,
  "total_amount": 4072.86,
  "vat_amount": 706.86,
  "vat_rate": "21%",
  "vendor": {
    "address": {
      "city": "Sevilla",
      "country": "ES",
      "postal_code": "41092",
      "street_name": "Innovaci\u00f3n",
      "street_number": "42",
      "street_type": "Avda."
    },
    "name": "TECNOLOG\u00cdA AVANZADA, S.A.",
    "tax_id": "A11223344"
  }
}
```


## Example 3

OCR Text:
```
DISTRIBUCIONES MEDITERRÁNEAS, SL
Polígono Industrial Sur, Nave 15
46980 Valencia
CIF: B55667788

Cliente:
Hostelería Costa, SL
Avda. Playa, 123
03001 Alicante
CIF: B11335577

FACTURA Nº: DM-2023-0456
Fecha: 07/05/2023

Producto              Cant.   Precio/u    Total
-----------------------------------------
Aceite de oliva 5L      20     22,50      450,00
Vino tinto (caja 6)     15     32,00      480,00
Patatas (saco 25kg)     10     18,75      187,50

Subtotal:                             1.117,50
IVA 10%:                                111,75
TOTAL EUROS:                          1.229,25

Forma de pago: Recibo domiciliado
Vencimiento: 22/05/2023
```

Correct Extraction:
```json
{
  "buyer": {
    "address": {
      "city": "Alicante",
      "country": "ES",
      "postal_code": "03001",
      "street_name": "Playa",
      "street_number": "123",
      "street_type": "Avda."
    },
    "name": "Hosteler\u00eda Costa, SL",
    "tax_id": "B11335577"
  },
  "currency": "EUR",
  "invoice_number": "DM-2023-0456",
  "issue_date": "2023-05-07",
  "line_items": [
    {
      "currency": "EUR",
      "description": "Aceite de oliva 5L",
      "item_type": "product",
      "line_total": 450.0,
      "qty": 20,
      "unit_price": 22.5
    },
    {
      "currency": "EUR",
      "description": "Vino tinto (caja 6)",
      "item_type": "product",
      "line_total": 480.0,
      "qty": 15,
      "unit_price": 32.0
    },
    {
      "currency": "EUR",
      "description": "Patatas (saco 25kg)",
      "item_type": "product",
      "line_total": 187.5,
      "qty": 10,
      "unit_price": 18.75
    }
  ],
  "payment_terms": {
    "due_date": "2023-05-22",
    "method": "recibo_domiciliado"
  },
  "taxable_base": 1117.5,
  "total_amount": 1229.25,
  "vat_amount": 111.75,
  "vat_rate": "10%",
  "vendor": {
    "address": {
      "city": "Valencia",
      "country": "ES",
      "postal_code": "46980",
      "street_name": "Pol\u00edgono Industrial Sur",
      "street_number": "Nave 15",
      "street_type": ""
    },
    "name": "DISTRIBUCIONES MEDITERR\u00c1NEAS, SL",
    "tax_id": "B55667788"
  }
}
```



# Output Format
Respond ONLY with a valid JSON object containing all extracted fields, formatted according to the schema.
Do not include any explanations, notes, or additional text outside of the JSON object. 
Use proper data types (numbers for numeric values, not strings), ISO date format, and structured nested objects. 
```

### User Message
```
OCR Text:

CARLOS LORENZO AVENIDA ISABEL DE VALOIS 90, BAJO A MADRID, MADRID, 28050 ES | Pagado | | :-- | | $N^{\circ}$ de referencia de pago 2suFZprY4TbarBvT0FSX | | Vendido por HONG KONG UGREEN LIMITED | | Fecha de la factura/Fecha | | de la entrega | | Número de la factura | | Total pendiente | | EI IVA ha sido declarado | Amazon Services Europe | | :-- | :-- | | por | S.a.r.L. | | IVA | LU19647148 | Si tienes preguntas sobre tus pedidos, visita https://www.amazon.es/contacto | Dirección de facturación | Dirección de envío | Vendido por | | :-- | :-- | :-- | | Carlos Lorenzo | Carlos Lorenzo | HONG KONG UGREEN LIMITED | | Avenida Isabel de Valois 90, Bajo A | Avenida Isabel de Valois 90, Bajo A | 19H WAN DI PLAZA | | Madrid, Madrid, 28050 | Madrid, Madrid, 28050 | 3 TAI YU STREET, SAN PO KONG, KL | | ES | ES | HONG KONG, HONG KONG, 999077 | | | | HK | # Información del pedido Fecha del pedido 27.04.2024 Número del pedido 171-4544162-9429147 ## Detalles de la factura | Descripción | Cant. | P. Unitario (IVA excluido) | IVA \% | P. Unitario (IVA incluido) | Precio total (IVA incluido) | | :--: | :--: | :--: | :--: | :--: | :--: | | UGREEN Revolok Pro 210 Docking Station USB C 10 En 1 Doble HDMI | 1 | $57,84 €$ | $21 \%$ | $69,99 €$ | $69,99 €$ | | 8K30Hz 4K60Hz Hub Adaptador USB C a 2 HDMI Ethernet Gigabit USB 3.0 | | | | | | | PD 100W Lector Tarjeta SD TF Compatible con MacBook Pro Air M2 M1 | | | | | | | B0BXDQS4BD | | | | | | | ASIN: B0BXDQS4BD | | | | | | | Envío | | $0,00 €$ | | $0,00 €$ | $0,00 €$ | | | Total | | | | $69,99 €$ | | | | IVA \% | Precio total (IVA excluido) | | IVA | | | | $21 \%$ | | $57,84 €$ | $12,15 €$ | | | Total | | | $57,84 €$ | $12,15 €$ | [^0] [^0]: ${ }^{\text {N }}$ Registro Integrado Industrial 6297 (AEE) : 1762 (Pilas y Acumuladores) LU-BIO-04 Amazon Services Europe S.a.r.l. 38 avenue John F. Kennedy, L-1805, Luxembourg R.C.S. Luxembourg; B 93815, Business license number: 100416 VAT number LU19647148 EI IVA ha sido declarado por Amazon en el país de entrega
CARLOS LORENZO AVENIDA ISABEL DE VALOIS 90, BAJO A MADRID, MADRID, 28050 ES | Pagado | | :-- | | $N^{\circ}$ de referencia de pago 2suFZprY4TbarBvT0FSX | | Vendido por Comfort Click Ltd | | Fecha de la factura/Fecha | | de la entrega 28.04.2024 | | Número de la factura 05-ASE-INV-ES-2024-33264321 | | Total pendiente 15,49 € | | El IVA ha sido declarado | Amazon Services Europe | | :-- | :-- | | por | S.a.r.L. | | IVA | LU19647148 | Si tienes preguntas sobre tus pedidos, visita https://www.amazon.es/contacto | Dirección de facturación | Dirección de envío | Vendido por | | :-- | :-- | :-- | | Carlos Lorenzo | Carlos Lorenzo | Comfort Click Ltd | | Avenida Isabel de Valois 90, Bajo A | Avenida Isabel de Valois 90, Bajo A | 106 Lower Addiscombe Road | | Madrid, Madrid, 28050 | Madrid, Madrid, 28050 | CROYDON, Surrey, CR0 6AD | | ES | | GB | # Información del pedido Fecha del pedido 27.04.2024 Número del pedido 171-4544162-9429147 ## Detalles de la factura | Descripción | Cant. | P. Unitario (IVA excluido) | IVA \% | P. Unitario (IVA incluido) | Precio total (IVA incluido) | | :--: | :--: | :--: | :--: | :--: | :--: | | Vinagre de Sidra de Manzana con la Madre 1860mg de Potencia 180 Cápsulas Veganas - Con Probióticos, Cúrcuma, Jengibre y Pimienta de Cayena, Suplemento Dietético Natural Para 2 Meses | 1 | $14,08 €$ | $10 \%$ | $15,49 €$ | $15,49 €$ | | | | | | | | | Cayena, Suplemento Dietético Natural Para 2 Meses | B081NCGQPB | | | | | | ASIN: B081NCGQPB | | | | | | | Envío | | $0,00 €$ | | $0,00 €$ | $0,00 €$ | | | Total | | | | $15,49 €$ | | | | IVA \% | Precio total (IVA excluido) | | IVA | | | | 10\% | | $14,08 €$ | $1,41 €$ | | | Total | | | $14,08 €$ | $1,41 €$ | [^0] [^0]: ${ }^{\text {N }}$ Registro Integrado Industrial 6297 (AEE) / 1762 (Pilas y Acumuladores) LU-BIO-04 Amazon Services Europe S.a.r.l. 38 avenue John F. Kennedy, L-1805, Luxembourg R.C.S. Luxembourg; B 93815, Business license number: 100416 VAT number LU19647148 El IVA ha sido declarado por Amazon en el país de entrega

Initial fields extracted:

{
  "invoice_number": "a",
  "total_eur": "1",
  "vat_amount": "8",
  "payment_terms": "2suFZprY4TbarBvT0FSX | | Vendido por HONG KONG UGREEN LIMITED | | Fecha de la factura/Fecha | | de la entrega | | Número de la factura | | Total pendiente | | EI IVA ha sido declarado | Amazon Services Europe | | :  -  - | :  -  - | | por | S.a.r.L. | | IVA | LU19647148 | Si tienes preguntas sobre tus pedidos, visita https : //www.amazon.es/contacto | Dirección de facturación | Dirección de envío | Vendido por | | :  -  - | :  -  - | :  -  - | | Carlos Lorenzo | Carlos Lorenzo | HONG KONG UGREEN LIMITED | | Avenida Isabel de Valois 90, Bajo A | Avenida Isabel de Valois 90, Bajo A | 19H WAN DI PLAZA | | Madrid, Madrid, 28050 | Madrid, Madrid, 28050 | 3 TAI YU STREET, SAN PO KONG, KL | | ES | ES | HONG KONG, HONG KONG, 999077 | | | | HK | # Información del pedido Fecha del pedido 27.04.2024 Número del pedido 171 - 4544162 - 9429147 ## Detalles de la factura | Descripción | Cant. | P. Unitario (IVA excluido) | IVA \\% | P. Unitario (IVA incluido) | Precio total (IVA incluido) | | :  -  -  : | :  -  -  : | :  -  -  : | :  -  -  : | :  -  -  : | :  -  -  : | | UGREEN Revolok Pro 210 Docking Station USB C 10 En 1 Doble HDMI | 1 | $57,84 €$ | $21 \\%$ | $69,99 €$ | $69,99 €$ | | 8K30Hz 4K60Hz Hub Adaptador USB C a 2 HDMI Ethernet Gigabit USB 3.0 | | | | | | | PD 100W Lector Tarjeta SD TF Compatible con MacBook Pro Air M2 M1 | | | | | | | B0BXDQS4BD | | | | | | | ASIN : B0BXDQS4BD | | | | | | | Envío | | $0,00 €$ | | $0,00 €$ | $0,00 €$ | | | Total | | | | $69,99 €$ | | | | IVA \\% | Precio total (IVA excluido) | | IVA | | | | $21 \\%$ | | $57,84 €$ | $12,15 €$ | | | Total | | | $57,84 €$ | $12,15 €$ | [^0] [^0] : ${ }^{\\text {N }}$ Registro Integrado Industrial 6297 (AEE) : 1762 (Pilas y Acumuladores) LU - BIO - 04 Amazon Services Europe S.a.r.l. 38 avenue John F. Kennedy, L - 1805, Luxembourg R.C.S. Luxembourg; B 93815, Business license number : 100416 VAT number LU19647148 EI IVA ha sido declarado por Amazon en el país de entrega CARLOS LORENZO AVENIDA ISABEL DE VALOIS 90, BAJO A MADRID, MADRID, 28050 ES | Pagado | | :  -  - | | $N^{\\circ}$ de referencia de pago 2suFZprY4TbarBvT0FSX | | Vendido por Comfort Click Ltd | | Fecha de la factura/Fecha | | de la entrega 28.04.2024 | | Número de la factura 05 - ASE - INV - ES - 2024 - 33264321 | | Total pendiente 15,49 € | | El IVA ha sido declarado | Amazon Services Europe | | :  -  - | :  -  - | | por | S.a.r.L. | | IVA | LU19647148 | Si tienes preguntas sobre tus pedidos, visita https : //www.amazon.es/contacto | Dirección de facturación | Dirección de envío | Vendido por | | :  -  - | :  -  - | :  -  - | | Carlos Lorenzo | Carlos Lorenzo | Comfort Click Ltd | | Avenida Isabel de Valois 90, Bajo A | Avenida Isabel de Valois 90, Bajo A | 106 Lower Addiscombe Road | | Madrid, Madrid, 28050 | Madrid, Madrid, 28050 | CROYDON, Surrey, CR0 6AD | | ES | | GB | # Información del pedido Fecha del pedido 27.04.2024 Número del pedido 171 - 4544162 - 9429147 ## Detalles de la factura | Descripción | Cant. | P. Unitario (IVA excluido) | IVA \\% | P. Unitario (IVA incluido) | Precio total (IVA incluido) | | :  -  -  : | :  -  -  : | :  -  -  : | :  -  -  : | :  -  -  : | :  -  -  : | | Vinagre de Sidra de Manzana con la Madre 1860mg de Potencia 180 Cápsulas Veganas - Con Probióticos, Cúrcuma, Jengibre y Pimienta de Cayena, Suplemento Dietético Natural Para 2 Meses | 1 | $14,08 €$ | $10 \\%$ | $15,49 €$ | $15,49 €$ | | | | | | | | | Cayena, Suplemento Dietético Natural Para 2 Meses | B081NCGQPB | | | | | | ASIN : B081NCGQPB | | | | | | | Envío | | $0,00 €$ | | $0,00 €$ | $0,00 €$ | | | Total | | | | $15,49 €$ | | | | IVA \\% | Precio total (IVA excluido) | | IVA | | | | 10\\% | | $14,08 €$ | $1,41 €$ | | | Total | | | $14,08 €$ | $1,41 €$ | [^0] [^0] : ${ }^{\\text {N }}$ Registro Integrado Industrial 6297 (AEE) / 1762 (Pilas y Acumuladores) LU - BIO - 04 Amazon Services Europe S.a.r.l. 38 avenue John F. Kennedy, L - 1805, Luxembourg R.C.S. Luxembourg; B 93815, Business license number : 100416 VAT number LU19647148 El IVA ha sido declarado por Amazon en el país de entrega",
  "metadata": {
    "extraction_method": "regex_heuristics",
    "extraction_timestamp": "2025-05-12T18:48:43.594741"
  }
}
```

### Initial Fields
```json
{
  "invoice_number": "a",
  "total_eur": "1",
  "vat_amount": "8",
  "payment_terms": "2suFZprY4TbarBvT0FSX | | Vendido por HONG KONG UGREEN LIMITED | | Fecha de la factura/Fecha | | de la entrega | | Número de la factura | | Total pendiente | | EI IVA ha sido declarado | Amazon Services Europe | | :  -  - | :  -  - | | por | S.a.r.L. | | IVA | LU19647148 | Si tienes preguntas sobre tus pedidos, visita https : //www.amazon.es/contacto | Dirección de facturación | Dirección de envío | Vendido por | | :  -  - | :  -  - | :  -  - | | Carlos Lorenzo | Carlos Lorenzo | HONG KONG UGREEN LIMITED | | Avenida Isabel de Valois 90, Bajo A | Avenida Isabel de Valois 90, Bajo A | 19H WAN DI PLAZA | | Madrid, Madrid, 28050 | Madrid, Madrid, 28050 | 3 TAI YU STREET, SAN PO KONG, KL | | ES | ES | HONG KONG, HONG KONG, 999077 | | | | HK | # Información del pedido Fecha del pedido 27.04.2024 Número del pedido 171 - 4544162 - 9429147 ## Detalles de la factura | Descripción | Cant. | P. Unitario (IVA excluido) | IVA \\% | P. Unitario (IVA incluido) | Precio total (IVA incluido) | | :  -  -  : | :  -  -  : | :  -  -  : | :  -  -  : | :  -  -  : | :  -  -  : | | UGREEN Revolok Pro 210 Docking Station USB C 10 En 1 Doble HDMI | 1 | $57,84 €$ | $21 \\%$ | $69,99 €$ | $69,99 €$ | | 8K30Hz 4K60Hz Hub Adaptador USB C a 2 HDMI Ethernet Gigabit USB 3.0 | | | | | | | PD 100W Lector Tarjeta SD TF Compatible con MacBook Pro Air M2 M1 | | | | | | | B0BXDQS4BD | | | | | | | ASIN : B0BXDQS4BD | | | | | | | Envío | | $0,00 €$ | | $0,00 €$ | $0,00 €$ | | | Total | | | | $69,99 €$ | | | | IVA \\% | Precio total (IVA excluido) | | IVA | | | | $21 \\%$ | | $57,84 €$ | $12,15 €$ | | | Total | | | $57,84 €$ | $12,15 €$ | [^0] [^0] : ${ }^{\\text {N }}$ Registro Integrado Industrial 6297 (AEE) : 1762 (Pilas y Acumuladores) LU - BIO - 04 Amazon Services Europe S.a.r.l. 38 avenue John F. Kennedy, L - 1805, Luxembourg R.C.S. Luxembourg; B 93815, Business license number : 100416 VAT number LU19647148 EI IVA ha sido declarado por Amazon en el país de entrega CARLOS LORENZO AVENIDA ISABEL DE VALOIS 90, BAJO A MADRID, MADRID, 28050 ES | Pagado | | :  -  - | | $N^{\\circ}$ de referencia de pago 2suFZprY4TbarBvT0FSX | | Vendido por Comfort Click Ltd | | Fecha de la factura/Fecha | | de la entrega 28.04.2024 | | Número de la factura 05 - ASE - INV - ES - 2024 - 33264321 | | Total pendiente 15,49 € | | El IVA ha sido declarado | Amazon Services Europe | | :  -  - | :  -  - | | por | S.a.r.L. | | IVA | LU19647148 | Si tienes preguntas sobre tus pedidos, visita https : //www.amazon.es/contacto | Dirección de facturación | Dirección de envío | Vendido por | | :  -  - | :  -  - | :  -  - | | Carlos Lorenzo | Carlos Lorenzo | Comfort Click Ltd | | Avenida Isabel de Valois 90, Bajo A | Avenida Isabel de Valois 90, Bajo A | 106 Lower Addiscombe Road | | Madrid, Madrid, 28050 | Madrid, Madrid, 28050 | CROYDON, Surrey, CR0 6AD | | ES | | GB | # Información del pedido Fecha del pedido 27.04.2024 Número del pedido 171 - 4544162 - 9429147 ## Detalles de la factura | Descripción | Cant. | P. Unitario (IVA excluido) | IVA \\% | P. Unitario (IVA incluido) | Precio total (IVA incluido) | | :  -  -  : | :  -  -  : | :  -  -  : | :  -  -  : | :  -  -  : | :  -  -  : | | Vinagre de Sidra de Manzana con la Madre 1860mg de Potencia 180 Cápsulas Veganas - Con Probióticos, Cúrcuma, Jengibre y Pimienta de Cayena, Suplemento Dietético Natural Para 2 Meses | 1 | $14,08 €$ | $10 \\%$ | $15,49 €$ | $15,49 €$ | | | | | | | | | Cayena, Suplemento Dietético Natural Para 2 Meses | B081NCGQPB | | | | | | ASIN : B081NCGQPB | | | | | | | Envío | | $0,00 €$ | | $0,00 €$ | $0,00 €$ | | | Total | | | | $15,49 €$ | | | | IVA \\% | Precio total (IVA excluido) | | IVA | | | | 10\\% | | $14,08 €$ | $1,41 €$ | | | Total | | | $14,08 €$ | $1,41 €$ | [^0] [^0] : ${ }^{\\text {N }}$ Registro Integrado Industrial 6297 (AEE) / 1762 (Pilas y Acumuladores) LU - BIO - 04 Amazon Services Europe S.a.r.l. 38 avenue John F. Kennedy, L - 1805, Luxembourg R.C.S. Luxembourg; B 93815, Business license number : 100416 VAT number LU19647148 El IVA ha sido declarado por Amazon en el país de entrega",
  "metadata": {
    "extraction_method": "regex_heuristics",
    "extraction_timestamp": "2025-05-12T18:48:43.594741"
  }
}
```

---

