# Checklist de publicación (todo lo marcado 🔒 exige autorización de Jose)

## Ya hecho (sin efectos externos)

- [x] Código completo, tests en verde (41), lint limpio.
- [x] Verificación en vivo: catálogo real (250 productos / 2.525 filas en 1,0 s) y detección real de
      `price_changed` contra una tienda pública.
- [x] ZIP de entrega: `catalogwatch-1.0.0.zip` (código, tests, README, Docker, licencia).
- [x] Ficha de venta en inglés y español, guion de vídeo/GIF, comandos de Stripe preparados.

## Pasos pendientes, en orden

1. [ ] Generar el GIF real: `asciinema rec demo.cast -c "bash scripts/demo.sh" && agg demo.cast catalogwatch.gif`.
2. [ ] Grabar el vídeo de 50 s siguiendo `03-demo-video-script.md` (rótulos, no voz si se prefiere).
3. 🔒 Crear producto + precio + payment link en Stripe **live** (`02-stripe-payment-link.md`, 4719
   céntimos = 39 € IVA incl.). Es dinero y fiscalidad: autorización explícita.
4. 🔒 Publicar la ficha (Whop y/o Gumroad). Si es Gumroad, **no activar Discover** (30 %).
5. 🔒 Primer outbound con el enlace: pasa por la cola (`/skill:outbound-send`), nunca a mano.
6. [ ] Fijar la métrica de corte a 30 días: ventas / conversaciones expuestas al producto.

## Antes de difundir, comprobar

- [ ] El ZIP se abre en una máquina limpia y el paso 1 del README funciona sin editar nada.
- [ ] `docker compose build` termina y `docker compose run --rm catalogwatch doctor` responde.
- [ ] El enlace de pago tiene `after_completion` a una página de gracias con la descarga.
- [ ] El email de recibo explica la entrega y el plazo de soporte (30 días, instalación).
- [ ] El token de Telegram no aparece en ningún vídeo, captura ni ficha.

## Riesgos que la ficha ya declara (no ocultar)

- Datos públicos únicamente; ToS y `robots.txt` de cada tienda son responsabilidad del comprador.
- Sin SLA ni mantenimiento; el respaldo JSON-LD devuelve menos campos.
- Duplicados de `handle::sku` se colapsan en el diff (se avisa por stderr).
