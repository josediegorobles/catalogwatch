# Demo: guion de vídeo (50 s) y GIF

Todo lo que se ve en pantalla sale de ejecuciones reales: `scripts/demo.sh` reproduce la secuencia
completa contra una tienda pública, sin claves.

## Grabación

Terminal a 100×30, tema oscuro, fuente monoespaciada 16 px. Graba solo la ventana del terminal: no
hace falta ni cámara ni diapositivas.

```bash
asciinema rec demo.cast -c "bash scripts/demo.sh"     # graba
agg demo.cast catalogwatch.gif                        # GIF para la ficha
```

Alternativa sin asciinema: QuickTime (macOS) o Screen Studio grabando la región del terminal, y
exportar GIF/MP4 a 1080p.

## Guion

| Tiempo | En pantalla | Voz / rótulo |
| --- | --- | --- |
| 0:00–0:05 | Terminal vacío, cursor parpadeando | "Vigilar precios de la competencia a mano cuesta horas cada semana." |
| 0:05–0:12 | `catalogwatch fetch --store https://www.allbirds.com --out catalog.csv --max-pages 1` | "Un comando: cualquier catálogo Shopify o WooCommerce a CSV." |
| 0:12–0:18 | Salida: `Fetched 2525 rows from 250 products (source: shopify)` en ~1 s | "250 productos, 2.525 filas de variante, un segundo." |
| 0:18–0:26 | `head -3 catalog.csv` con las columnas visibles (sku, price, available, image_url) | "Una fila por variante: SKU, precio, precio anterior, stock, imagen, URL." |
| 0:26–0:36 | `catalogwatch watch --store ... --out changes.csv --state-dir state` dos veces: primera 2524 cambios, segunda 0 | "La segunda vez solo te cuenta lo que ha cambiado de verdad." |
| 0:36–0:44 | Tercera ejecución tras tocar el snapshot: fila `price_changed, ...,130.00` | "Y te dice el SKU exacto: de 130,00 a 99,00." |
| 0:44–0:50 | `catalogwatch watch ... --telegram --dry-run` con el mensaje formateado | "Aviso a Telegram si quieres. 39 € una vez, sin cuotas por producto." |

Rótulo final: **CatalogWatch — 39 €, licencia perpetua, código fuente incluido.**

## Texto de respaldo (para la descripción del vídeo)

> CatalogWatch lee el endpoint público que toda tienda Shopify y WooCommerce ya publica: sin
> navegador, sin selectores y sin cuotas por producto. Exporta el catálogo a CSV y genera un informe
> de cambios por SKU (precio, stock, altas y bajas) con aviso opcional a Telegram. Probado en vivo:
> 250 productos en 1,0 s. 39 € pago único, licencia comercial para un negocio, tiendas y
> ejecuciones ilimitadas.

## Qué no grabar

- No grabar la configuración de Telegram con el token visible (censurar el token y el chat id).
- No grabar contra la tienda de un cliente real sin permiso: usa una tienda pública de referencia.
- No prometer detección en tiempo real: CatalogWatch corre cuando lo programas (cron, LaunchAgent).
