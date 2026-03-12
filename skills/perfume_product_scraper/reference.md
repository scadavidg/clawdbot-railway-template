# Medusa Product Schema & Perfume Scraper Reference

## Product (Medusa-compatible)

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| id | string | yes | Generate deterministic hash from URL if missing |
| title | string | yes | |
| subtitle | string | no | |
| description | string | no | HTML stripped |
| handle | string | yes | Slug from title (lowercase, hyphens) |
| status | string | yes | Default: `"published"` |
| thumbnail | string | no | Absolute URL; first image if missing |
| images | array | no | See Images below |
| weight | number | no | |
| width | number | no | |
| height | number | no | |
| length | number | no | |
| origin_country | string | no | |
| material | string | no | |
| metadata | object | no | Perfume-specific and custom key-value |
| created_at | string | no | ISO 8601 |
| updated_at | string | no | ISO 8601 |
| tags | array | no | e.g. `[{ "id": "...", "value": "..." }]` |
| categories | array | no | e.g. `[{ "id": "...", "name": "...", "handle": "..." }]` |
| options | array | no | Product options (e.g. Size) |
| variants | array | no | One per size/variant |

## Images

Each image object:

```json
{
  "id": "string (unique)",
  "url": "string (absolute URL)",
  "rank": "number (0-based order)"
}
```

- Deduplicate by `url`.
- Assign `rank` by order of appearance on the page.
- Generate `id` if missing (e.g. hash of URL or `img_` + index).

## Options

Product options (e.g. Size for perfumes):

```json
{
  "id": "string (unique)",
  "title": "Size",
  "values": [
    { "value": "30ml" },
    { "value": "50ml" },
    { "value": "100ml" }
  ]
}
```

- One option per dimension (Size, Concentration, etc.).
- `values` must match variant option values.

## Variants

Perfume variants (e.g. bottle sizes):

| Field | Type | Default / Notes |
|-------|------|------------------|
| id | string | Required; unique |
| title | string | e.g. "Eau de Parfum 50ml" |
| sku | string | Generate if missing (e.g. handle-size) |
| barcode / ean / upc | string | If available |
| weight, length, width, height | number | Optional |
| inventory_quantity | number | Default: 0 if unknown |
| allow_backorder | boolean | false |
| manage_inventory | boolean | true |
| variant_rank | number | Order (0-based) |
| thumbnail | string | Optional image URL |
| metadata | object | Optional |

Each variant should reference the product's options (e.g. option "Size" → value "50ml").

## Perfume metadata (product.metadata)

Extract when available and put under `metadata`:

| Key | Type | Example |
|-----|------|--------|
| brand | string | "Dior" |
| concentration | string | "EDT", "EDP", "Parfum" |
| gender | string | "men", "women", "unisex" |
| fragrance_family | string | "Woody", "Fresh" |
| top_notes | string[] | ["Bergamot", "Pepper"] |
| middle_notes | string[] | ["Lavender", "Geranium"] |
| base_notes | string[] | ["Vanilla", "Ambroxan"] |
| launch_year | number | 2015 |

## Example output

```json
{
  "products": [
    {
      "id": "prod_a1b2c3",
      "title": "Dior Sauvage Eau de Parfum",
      "subtitle": null,
      "description": "A bold and fresh fragrance...",
      "handle": "dior-sauvage-eau-de-parfum",
      "status": "published",
      "thumbnail": "https://example.com/img/main.jpg",
      "images": [
        { "id": "img_0", "url": "https://example.com/img/main.jpg", "rank": 0 },
        { "id": "img_1", "url": "https://example.com/img/alt.jpg", "rank": 1 }
      ],
      "weight": null,
      "width": null,
      "height": null,
      "length": null,
      "origin_country": null,
      "material": null,
      "metadata": {
        "brand": "Dior",
        "concentration": "EDP",
        "gender": "men",
        "fragrance_family": "Fresh Spicy",
        "top_notes": ["Bergamot", "Pepper"],
        "middle_notes": ["Lavender", "Geranium"],
        "base_notes": ["Vanilla", "Ambroxan"],
        "launch_year": 2015
      },
      "created_at": null,
      "updated_at": null,
      "tags": [],
      "categories": [],
      "options": [
        {
          "id": "opt_1",
          "title": "Size",
          "values": [
            { "value": "60ml" },
            { "value": "100ml" }
          ]
        }
      ],
      "variants": [
        {
          "id": "var_1",
          "title": "Eau de Parfum 60ml",
          "sku": "dior-sauvage-edp-60ml",
          "barcode": null,
          "weight": null,
          "length": null,
          "width": null,
          "height": null,
          "inventory_quantity": 0,
          "allow_backorder": false,
          "manage_inventory": true,
          "variant_rank": 0,
          "thumbnail": null,
          "metadata": {}
        },
        {
          "id": "var_2",
          "title": "Eau de Parfum 100ml",
          "sku": "dior-sauvage-edp-100ml",
          "barcode": null,
          "weight": null,
          "length": null,
          "width": null,
          "height": null,
          "inventory_quantity": 0,
          "allow_backorder": false,
          "manage_inventory": true,
          "variant_rank": 1,
          "thumbnail": null,
          "metadata": {}
        }
      ]
    }
  ]
}
```

## Normalization rules

- **Descriptions**: Remove all HTML tags; collapse whitespace.
- **URLs**: Convert relative to absolute using the product page URL as base.
- **Images**: Deduplicate by URL; assign unique `id` and `rank` by order.
- **IDs**: All `id` values must be unique (product, images, options, variants). Use deterministic hashes (e.g. from URL + role) when generating.
- **Handle**: From title: lowercase, replace spaces/special chars with `-`, collapse multiple hyphens.
- **Missing fields**: Omit optional fields or use defaults from this reference; never break required fields.
