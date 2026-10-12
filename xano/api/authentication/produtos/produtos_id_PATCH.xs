// Edit produtos record
query "produtos/{produtos_id}" verb=PATCH {
  api_group = "Authentication"

  input {
    int produtos_id? filters=min:1
    dblink {
      table = "produtos"
    }
  }

  stack {
    util.get_raw_input {
      encoding = "json"
      exclude_middleware = false
    } as $raw_input
  
    db.patch produtos {
      field_name = "id"
      field_value = $input.produtos_id
      data = `$input|pick:($raw_input|keys)`|filter_null|filter_empty_text
    } as $produtos
  }

  response = $produtos
  guid = "mGhio7DOKrutqUqsnX012mb9OBw"
}