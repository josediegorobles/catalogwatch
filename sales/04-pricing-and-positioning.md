# Precio, posicionamiento y evidencia (2026-09-21)

## Veredicto de la elección A/B

**Elegida: Opción B, reencuadrada** — extracción de catálogo + informe de cambios por SKU.
**Descartada: Opción A** (bot de alertas Telegram) — su sustituto es gratis, maduro y ya trae
Telegram: `changedetection.io` es MIT, self-hosted, ilimitado, con notificaciones Telegram
incorporadas (comparativas 2026: `pagecrawl.io/alternative/changedetection-io`,
`getsignalhub.com/blog/the-best-web-monitoring-tools-in-2026`, `visualping.io/blog/best-free-website-change-detection-monitoring-tools`).
Construir A era vender una versión peor de algo gratis.

## La cuña defendible (una sola)

**Un pago, ejecuciones ilimitadas, sin coste por producto y con histórico por SKU en un fichero
tuyo.** Es lo único que los sustitutos no dan:

| Alternativa | Coste para 10 catálogos × 2.500 SKUs | Qué te falta |
| --- | --- | --- |
| API de scraping tipo Apify (Shopify) | 1,50–6,00 $/1.000 productos ⇒ ~25–100 $/mes (`use-apify.com`, verificado 2026-09-09; `apify.com/makework36`) | Pagas por producto cada mes |
| Matrixify (tu propia tienda) | 20 $/mes (5K productos) hasta 200 $ (`apps.shopify.com/excel-export-import`) | No sirve para catálogos ajenos |
| changedetection.io | Gratis self-hosted; 8,99 $/mes gestionado | Diff de texto, no de SKU; una URL por monitor |
| Fiverr | ~30 $ por catálogo puntual | Turnaround humano y cero histórico |
| **CatalogWatch** | **39 € una vez** | Nada: CSV + informe de cambios + Telegram |

ROI real medido: 250 productos / 2.525 filas en **1,0 s**; 500 productos en 2,1 s (tienda pública,
2026-09-21). Una pasada manual por catálogo son ~20 min; diez catálogos al mes son 8–15 h.

## Lo que la evidencia también dice (y va contra nosotros)

1. **El endpoint es conocimiento público.** Los guías 2026 enseñan `/products.json` como truco
   gratis (`beaconmon.com`, `storesentry.app`). No vendemos el endpoint: vendemos el informe de
   cambios, el histórico y el cero-mantenimiento.
2. **El nicho está lleno de herramientas indie de monitorización de precios** (`pricesway.com`,
   `undercut-price-monitor.com`, `thepricekit.com`). El precio no lo fija CatalogWatch: lo fija ese
   mercado. Por eso 39 € y no 99 €.
3. **El cuello de botella es la distribución, no el código.** `gumroad_sales = 0` con el pack
   anterior y `x402_payments = 7` (`business/telemetry/state.json`, 2026-09-21) dicen lo mismo: lo
   que se distribuye por conversación se cobra; lo que se cuelga en un marketplace a la espera de
   descubrimiento, no.
4. **Gumroad cobra 10 % + 0,50 $ directo y 30 % vía Discover** (`gumroad.com/pricing`, 2026). Para
   un producto sin audiencia, pagar 30 % por un descubrimiento que no ocurre es el peor trato del
   catálogo de canales (`business/canales-producto-digital.md`).

## Recomendación (una)

**Distribuir por superficies de entrada (buscador → ficha), no por escaparates ni por outbound: repo público, actor gratuito en Apify Store y herramienta web con captura de correo en josedrobles.com.** Porqué: el comprador del CSV llega buscando y lo que se cobra es lo que el buscador no resuelve (histórico de cambios por SKU); los canales con conversación humana (x402, 7 pagos) ya están ocupados por el ICP industrial/legal y abrir el ICP e-commerce sería un frente nuevo. El detalle, la economía de cada superficie y las condiciones de corte están en `06-distribution-plan.md`.

El precio de 39 € no aparece en el outbound D1/D2/Whop: diluiría el ancla de 390 € de la Sesión A.

## Condición de revalidación

Corte a 30 días (detalle en `06-distribution-plan.md`): sin ≥20 correos capturados y ninguna
licencia cobrada, el activo se congela publicado (coste 0) y no recibe más ingeniería sin una
petición pagada previa.
