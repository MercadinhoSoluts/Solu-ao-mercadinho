table preco {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
  
    int produtos_id? {
      table = "produtos"
    }
  
    decimal preco_unitario?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
  ]

  guid = "KaUWkImHtHfRz5LoGeVL1sYxNRk"
}