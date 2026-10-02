table products {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    text? barcode?
    text name
    int? category_id?
    int sale_price_cents
    text unit
    decimal minimum_stock
    bool is_perishable
    bool is_active?=true
    int? created_by?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "barcode"}]}
    {type: "btree", field: [{name: "name"}]}
  ]

  guid = "CYsa6rWjhGLnpRwY7b0GSv4mHMY"
}