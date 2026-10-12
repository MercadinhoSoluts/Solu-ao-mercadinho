// Update produtos record
query "produtos/{produtos_id}" verb=PUT {
  api_group = "CRUD Produtos"

  input {
    int produtos_id? filters=min:1
    dblink {
      table = "produtos"
    }
  }

  stack {
    db.edit produtos {
      field_name = "id"
      field_value = $input.produtos_id
      enforce_hidden_fields = false
      data = {
        nome : $input.nome
        marca: $input.marca
        peso : $input.peso
      }
    } as $model
  }

  response = $model
  guid = "CeJZcXKvcPY3ChW3ESRI555RUkk"
}