# Ficha de venta — Español (Kwork / Whop / Wallapop Pro / DM)

**Título:** Catálogo de la competencia a CSV + avisos de cambio de precio

**Subtítulo:** Exporta cualquier catálogo Shopify o WooCommerce a CSV con un comando y recibe en
Telegram qué SKUs han cambiado de precio o de stock. Sin navegador, sin cuotas.

**Precio:** 39 € pago único (IVA incluido para compradores UE vía merchant of record).

---

## Descripción

**Vigila 10 catálogos de la competencia en lo que tardas en hacerte un café.**

CatalogWatch lee el endpoint público que toda tienda Shopify y WooCommerce ya publica, lo escribe
en un CSV limpio (una fila por variante: SKU, precio, precio anterior, stock, imagen, URL) y te
dice exactamente qué ha cambiado desde la última vez.

Medido en una tienda real: **250 productos / 2.525 filas de variante en 1,0 segundos.**

```bash
catalogwatch fetch --store https://competidor.com --out catalogo.csv
catalogwatch watch --store https://competidor.com --out cambios.csv --telegram
```

**Qué incluye**

- Informe de cambios por `handle::sku` (`added`, `removed`, `price_changed`, `stock_changed`), de
  modo que el histórico sobrevive a cambios de título o de plantilla.
- Aviso opcional a Telegram, con `--dry-run` para probarlo sin enviar nada.
- Reintentos con backoff exponencial y `Retry-After`, User-Agent identificable y pausa entre
  páginas: no te bloquean por abuso.
- Se ejecuta en tu máquina o en Docker, con la programación que tú decidas.
- Código fuente completo, 41 tests sin red, README, `.env.example`, Dockerfile y script de demo.
- Licencia comercial: un negocio, tiendas y ejecuciones ilimitadas.

**Para quién es**

- Tiendas que revisan precios de la competencia a mano cada semana.
- Agencias que necesitan el catálogo de un cliente o de un competidor en Excel en segundos.
- Dropshipping y arbitraje esperando reposiciones y bajadas de precio.
- Gente de datos que quiere el CSV, no otra suscripción con dashboard.

**Por qué no una API de scraping**

Porque pagas por producto y para siempre: las típicas cobran 1,50–6,00 $ por cada 1.000 productos,
así que diez catálogos de 2.500 SKUs cuestan ~25–100 $ **cada mes**. CatalogWatch se paga una vez,
corre en local y el histórico es un fichero tuyo.

**Por qué no changedetection.io**

Porque vigila páginas y compara texto: te avisa de que "algo ha cambiado" en el HTML. CatalogWatch
entiende de productos: te dice "el SKU A11768M080 ha bajado de 130,00 a 99,00".

**Límites, sin adornos**

- Solo datos públicos: catálogos tras login quedan fuera.
- Si la tienda desactivó su endpoint público, hay respaldo por JSON-LD en la página de listado, con
  menos campos (sin opciones de variante ni cantidad de stock).
- Una moneda por tienda, tal y como la publica.
- Sin SLA ni alojamiento: no hay nada que mantener porque lee la API pública de la propia tienda.

**Requisitos:** Python 3.10+ (o Docker) y una máquina que alcance la web de la tienda.

**Soporte:** instalación por email durante 30 días. Después, nada que mantener.
