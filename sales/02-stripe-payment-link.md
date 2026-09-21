# Enlace de pago con Stripe

> **EJECUTADO 2026-09-21 (autorizado por Jose).** Cuenta `RoblesAI · live` (`acct_1Tigz7PRaXEe25Cg`).
> - Producto: `prod_VIkxSGAnEQ98zH` (CatalogWatch)
> - Precio: `price_1UI9RzPRaXEe25Cg3eXjSt6G` (4719 céntimos EUR = 39 € IVA incl.)
> - Payment link: `plink_1UI9S0PRaXEe25Cg8ofhD9K9` → **<https://buy.stripe.com/8x200lfkEbyffbd3SifrW09>**
> - `after_completion`: redirect a <https://github.com/josediegorobles/catalogwatch/releases/latest>
> - Pausar en un segundo: `stripe payment_links update plink_1UI9S0PRaXEe25Cg8ofhD9K9 --live -d "active=false"`

Los comandos siguientes quedan como registro reproducible de lo ejecutado.

Precio: **39 € IVA incluido** → `--unit-amount 4719` (39 € + 21 % IVA = 47,19 € = 4719 céntimos).

## 0. Comprobar cuenta y modo

```bash
stripe config --list
# El banner ▸ Running in <cuenta> · <modo> va a stderr. Leerlo antes de seguir.
```

## 1. Crear producto, precio y payment link (live)

```bash
P=$(stripe products create --live \
      --name "CatalogWatch" \
      --description "Export any Shopify/WooCommerce catalog to CSV and get SKU-level price and stock change alerts. One-time licence, one business, unlimited stores." \
      -d "metadata[product]=catalogwatch" -d "metadata[version]=1.0.0" \
    | sed -n '/^{/,$p' | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")

PR=$(stripe prices create --live --product "$P" --unit-amount 4719 --currency eur \
       -d "nickname=CatalogWatch v1.0 (IVA incl.)" \
     | sed -n '/^{/,$p' | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")

L=$(stripe payment_links create --live \
      -d "line_items[0][price]=$PR" -d "line_items[0][quantity]=1" \
      -d "after_completion[type]=redirect" \
      -d "after_completion[redirect][url]=https://josedrobles.com/catalogwatch/gracias" \
    | sed -n '/^{/,$p' | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")

echo "payment link: $L"
```

## 2. Verificar antes de difundir

```bash
stripe payment_links retrieve "$L" --live | sed -n '/^{/,$p' | python3 -m json.tool | head -30
```

## 3. Pausar el enlace en un segundo (gatillo con seguro)

```bash
stripe payment_links update "$L" --live -d "active=false"
```

## 4. Entrega

- Entrega manual: adjuntar `catalogwatch-1.0.0.zip` en el email de confirmación (Stripe envía un
  recibo; el ZIP va en un mensaje propio o en un enlace de descarga).
- Entrega automática: subir el ZIP a Drive/Cloudflare R2 y pegar el enlace en el email de recibo, o
  usar la `after_completion` redirect a una página de gracias con la descarga.

## 5. Qué NO hacer sin autorización

- No crear el producto/precio/enlace en `--live`.
- No publicar el enlace en Gumroad, Whop, LinkedIn, DMs ni en ninguna web.
- No enviar ningún mensaje con el enlace: todo outbound pasa por la cola (`outbound-send`).
