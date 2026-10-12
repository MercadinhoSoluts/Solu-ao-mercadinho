table codigobarra {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
  
    int produtos_id? {
      table = "produtos"
    }
  
    text codigo_de_barras? filters=trim
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {
      type : "btree|unique"
      field: [{name: "codigo_de_barras", op: "asc"}]
    }
  ]

  guid = "GEPGpArlH3YzPKnQoHZa28sPGYI"
}