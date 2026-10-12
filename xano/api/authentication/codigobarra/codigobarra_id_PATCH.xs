// Edit codigobarra record
query "codigobarra/{codigobarra_id}" verb=PATCH {
  api_group = "Authentication"

  input {
    int codigobarra_id? filters=min:1
    dblink {
      table = "codigobarra"
    }
  }

  stack {
    util.get_raw_input {
      encoding = "json"
      exclude_middleware = false
    } as $raw_input
  
    db.patch codigobarra {
      field_name = "id"
      field_value = $input.codigobarra_id
      data = `$input|pick:($raw_input|keys)`|filter_null|filter_empty_text
    } as $codigobarra
  }

  response = $codigobarra
  guid = "7cwhsBq7YJT_0cJY9HdAQBsmU0Q"
}