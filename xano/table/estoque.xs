table estoque {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
  
    int produtos_id? {
      table = "produtos"
    }
  
    int lote?
    int unidades?
    date? validade?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
  ]

  guid = "6K_1niCRKrx7TJFO9dCTdUxPKp4"
}