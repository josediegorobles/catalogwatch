# Plan de distribución — CatalogWatch (30 días)

> Interno. Este documento no va en el ZIP del comprador (excluido en el build).

## Veredicto en una línea

**CatalogWatch se distribuye por superficies de entrada (buscador → ficha), no por escaparates ni por
outbound:** el comprador del CSV gratis llega buscando, y lo que se cobra es lo que el buscador no
resuelve — el histórico de cambios por SKU.

---

## 1. La premisa que había que corregir

Un consultor Sub-Frontier propuso usar CatalogWatch como munición de apertura en el outbound D1 de
LinkedIn ("informe de deltas del catálogo público del prospecto"). **La premisa es falsa:** el ICP
vivo de D1/D2 son *directores industriales, de operaciones y de planta de pymes industriales
españolas*, más startups AI y despachos legales (`prospeccion-d1-d2/guion-llamada-d1.md`). Esos
prospectos **no tienen catálogo de producto público**: no hay informe que enviarles.

Consecuencia: para que este activo sirva al outbound actual habría que abrir un ICP nuevo
(e-commerce) y, con él, un frente nuevo. `current-focus.md` dice explícitamente que la semana no abre
frentes nuevos. Así que **el outbound no es el canal**; sí lo es todo lo que ocurre sin consumir
capacidad de conversación.

## 2. Dos compradores, dos puertas (no mezclar)

| Comprador | Qué quiere | Puerta | Precio |
| --- | --- | --- | --- |
| Agencia / freelance técnico / dropshipper con CLI | Extraer y **vigilar** catálogos de sus clientes, ilimitado | Licencia autohospedada | **39 € una vez** |
| Dueño de tienda sin perfil técnico | Que alguien se lo vigile y le avise | (solo si hay demanda entrante) servicio gestionado | 29 €/mes por tienda |

El precio de 39 € **no entra nunca** en el outbound D1/D2/Whop: diluye el ancla de 390 € de la Sesión
A por 39 €. Si algún día aparece un prospecto e-commerce en esa motion, el informe se **regala**
dentro de la Sesión A; la licencia se vende solo a quien pregunta "¿me lo puedo quedar?".

## 3. Las tres superficies de entrada (cero outbound, cuentas ya existentes)

### A. Ficha en Apify Store (funnel, no facturación)
- **Por qué:** las fichas de Apify Store rankean en Google para búsquedas de scraper (`blog.apify.com/building-98-actors-on-apify-store`, 2026) y hay 70.000+ actores, así que es una superficie de descubrimiento real, no un escaparate muerto.
- **Cómo:** actor gratuito "Shopify & WooCommerce catalog → CSV" (imagen Docker con el código actual) cuyo README enlaza a la licencia autohospedada para el *watch*.
- **Economía:** Apify paga el 80 % y, desde oct-2026, **solo pay-per-event** (`docs.apify.com/academy/.../how-actor-monetization-works`; `blog.apify.com/standardizing-actor-pricing`). Por eso **no** se monetiza ahí: un pago único de 39 € no cabe en su modelo. Es escaparate.
- **Verificar antes de publicar:** si las condiciones de publicación (`docs.apify.com/legal/store-publishing-terms-and-conditions`) permiten enlazar a un producto propio de pago. **No verificado.**

### B. Herramienta web gratis en josedrobles.com (captura de correo con trabajo real)
- **Por qué:** el carril web/captación ya está activo y **capturó 0 correos con 4 lead magnets** (9–29 visitas reales/semana, `current-focus.md` 2026-09-21). El problema no era el tráfico: era que los magnets no hacían nada. Pegar la URL de una tienda y recibir el CSV **hace algo**.
- **Cómo:** Worker en Cloudflare (stack ya montado: Workers + D1 + Resend) que llama al mismo motor; correo obligatorio para recibir el CSV, con la licencia de 39 € y el servicio de 29 €/mes como siguiente paso.
- **Reparto freemium correcto:** gratis = `fetch` (la parte comoditizada, que ya está regalada en blogs de 2026); de pago = `watch` + histórico + Telegram (la cuña).

### C. Repo público en GitHub (superficie de desarrollador)
- **Por qué:** el comprador de la licencia es técnico y busca en GitHub antes que en Gumroad.
- **Cómo:** repo con README + GIF de 50 s + topics, y el modo `watch` como parte de pago. Contraindicación asumida: el fork es gratis; por eso el repo lleva solo el motor de extracción y la licencia cubre el histórico, el soporte y el uso comercial.

## 4. Lo que NO se hace en 30 días (con la razón)

| Descartado | Por qué |
| --- | --- |
| Gumroad / Whop como canal de descubrimiento | 10 % + 0,50 $ directo y **30 % en Discover** (`gumroad.com/pricing`); el pack anterior acumula **0 ventas** (`business/telemetry/state.json`) |
| Product Hunt / newsletters | 487 de 500 lanzamientos analizados acaban muertos (`reddit.com/r/SaaS/comments/1mnc3nu`); es un pico, no un canal |
| r/shopify y similares | **Autopromoción prohibida** (`leadsrover.io/subreddits/r/shopify`, verificado 2026-05-30) |
| Kwork / Fiverr | Kwork: 20 % + 4,5 % de retirada y mercado CIS; Fiverr ya tiene el servicio a ~30 $ (veredicto lote 2) |
| Shopify App Store | Económicamente el mejor (0 % hasta 1 M$, luego 15 % — `shopify.dev/docs/apps/launch/distribution/revenue-share`) y allí viven competidores a **49–229 $/mes** (Prisync, PriceMole), pero exige app embebida con OAuth y billing: es un negocio de 6–12 meses, no un sprint. Queda como opción estratégica, no como plan de 30 días |
| Vender la licencia en el outbound D1/D2 | Diluye el ancla de 390 € |
| Más ingeniería (Telegram v2, billing, multi-tenant) | El producto está terminado; el cuello de botella no es el código |

## 5. Medición y corte (vía `automation/scripts/caja.py`)

| Día | Medida | Corte |
| --- | --- | --- |
| 14 | Visitas a la herramienta web, correos capturados, runs del actor Apify | <30 visitas o <3 correos ⇒ el problema es el magnet, no el tráfico: reescribe la página antes de gastar más |
| 30 | Correos capturados y licencias cobradas en Stripe live | <20 correos y 0 licencias ⇒ el activo pasa a congelado: se queda publicado (coste 0) y no recibe más tiempo |
| 30 | Si aparece demanda de "vigílame tú" (≥3 peticiones) | Abrir el servicio gestionado a 29 €/mes solo entonces |

**Ningún euro de gasto:** las tres superficies usan cuentas y stack existentes (Apify, Cloudflare,
Stripe). No se compra tráfico ni se paga listado.

## 6. Acción del día 0

1. Publicar el repo público con el motor de extracción y el GIF (`scripts/demo.sh` ya lo produce).
2. Envolver el motor como actor de Apify (imagen Docker) y publicarlo gratis, tras verificar la
   condición de enlaces externos.
3. Worker + página en josedrobles.com con captura de correo.

Coste estimado: ≤1 día por superficie. Ninguna de las tres requiere una conversación ni una cuenta
nueva, y las tres se pueden medir sin pedirle nada a nadie.
