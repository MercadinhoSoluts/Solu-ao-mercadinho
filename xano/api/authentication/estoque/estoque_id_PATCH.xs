// Edit estoque record
query "estoque/{estoque_id}" verb=PATCH {
  api_group = "Authentication"

  input {
    int estoque_id? filters=min:1
    dblink {
      table = "estoque"
    }
  }

  stack {
    util.get_raw_input {
      encoding = "json"
      exclude_middleware = false
    } as $raw_input
  
    db.patch estoque {
      field_name = "id"
      field_value = $input.estoque_id
      data = `$input|pick:($raw_input|keys)`|filter_null|filter_empty_text
    } as $estoque
  }

  response = $estoque
  guid = "n_dVJ6kqVBelBX_M6yIRV6jgh0s"
}