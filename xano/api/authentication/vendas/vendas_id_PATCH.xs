// Edit vendas record
query "vendas/{vendas_id}" verb=PATCH {
  api_group = "Authentication"

  input {
    int vendas_id? filters=min:1
    dblink {
      table = "preco"
    }
  }

  stack {
    util.get_raw_input {
      encoding = "json"
      exclude_middleware = false
    } as $raw_input
  
    db.patch preco {
      field_name = "id"
      field_value = $input.vendas_id
      data = `$input|pick:($raw_input|keys)`|filter_null|filter_empty_text
    } as $vendas
  }

  response = $vendas
  guid = "mRczssr3Kc-HF61jgVXvH_r7aHo"
}