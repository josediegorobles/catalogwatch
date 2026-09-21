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

## 3. Las superficies de entrada (cero outbound, cuentas ya existentes)

### A. ~~Ficha en Apify Store~~ → **prohibido por sus condiciones** (sustituido por el repo)
- **Hallazgo (2026-09-21):** las condiciones de publicación de Apify Store prohíben *"directly or indirectly offer, link to, or promote any product or service outside of the Platform in your Actors or in any other content you publish on Apify Store, including in the Actor's readme, description, issues, or reviews"* (`docs.apify.com/legal/store-publishing-terms-and-conditions`, §2.2.4.2(i), actualizado 15-sep-2026).
- Consecuencia: el actor gratuito como embudo hacia la licencia de 39 € **no se puede hacer**. Publicar un actor *de pago* exigiría pay-per-event obligatorio desde oct-2026 (`blog.apify.com/standardizing-actor-pricing`), es decir, vender el CSV a céntimos por ejecución: otro negocio, y con 70.000+ actores de competencia. **Descartado.**
- **Superficie que lo sustituye: el repo público de GitHub** (indexado, enlaza a donde quiera, y es donde busca el comprador técnico).

### B. Herramienta web gratis en josedrobles.com (captura de correo con trabajo real) — **no hecha, a propósito**
- **Por qué se propuso:** el carril web/captación ya está activo y **capturó 0 correos con 4 lead magnets** (9–29 visitas reales/semana, `current-focus.md` 2026-09-21). El problema no era el tráfico: era que los magnets no hacían nada.
- **Por qué no se hizo:** el tráfico de esa web es de pymes industriales, no de e-commerce (el ICP vivo de D1/D2 son directores de planta y despachos legales), así que un magnet de catálogos competidores desalinea el posicionamiento del sitio, y 9–29 visitas/semana no arreglan ninguna métrica. Se retoma solo si el repo genera tráfico real que convenga capturar.

### C. Repo público en GitHub (superficie de desarrollador) — **publicado 2026-09-21**
- **Por qué:** el comprador de la licencia es técnico y busca en GitHub antes que en Gumroad; además las páginas de GitHub se indexan y no hay plataforma que cobre comisión.
- **Cómo:** repo público <https://github.com/josediegorobles/catalogwatch> con README + GIF de 50 s + topics, licencia comercial (gratis para uso no comercial, 39 € para uso comercial) y el enlace de pago en el README. Release `v1.0.0` con el ZIP como asset, que es el destino del `after_completion` de Stripe.
- Contraindicación asumida: el código es copiable. El precio no protege el código, protege el uso comercial y el soporte de instalación; con este volumen esperado es el trato correcto.

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

## 6. Acción del día 0 — **ejecutada 2026-09-21**

1. [x] Repo público con el código, README, licencia comercial y GIF pendiente (`scripts/demo.sh` ya produce la secuencia para grabarlo).
2. [x] Producto + precio + payment link en Stripe live (39 € IVA incl.) con `after_completion` a la release.
3. [x] Release `v1.0.0` con el ZIP como asset (es lo que recibe el comprador al pagar).
4. [ ] GIF y vídeo de 50 s (requiere grabar pantalla; `agg`/asciinema no están instalados).
5. [ ] Actor de Apify: descartado por sus condiciones (§2.2.4.2(i)).
6. [ ] Herramienta web con captura de correo: aplazada a propósito (desalinea el posicionamiento y no hay tráfico que capturar).

Lo ejecutado se midió sin pedirle nada a nadie: repo, enlace de pago y release no requieren conversación ni gasto.
