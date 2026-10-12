// Add produtos record
query produtos verb=POST {
  api_group = "CRUD Produtos"

  input {
    dblink {
      table = "produtos"
    }
  }

  stack {
    db.add produtos {
      enforce_hidden_fields = false
      data = {
        created_at: "now"
        nome      : $input.nome
        marca     : $input.marca
        peso      : $input.peso
      }
    } as $model
  }

  response = $model
  guid = "QtTniozSh-sDjokvtiDVVUZvbiE"
}