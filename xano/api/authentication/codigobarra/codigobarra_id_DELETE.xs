// Delete codigobarra record.
query "codigobarra/{codigobarra_id}" verb=DELETE {
  api_group = "Authentication"

  input {
    int codigobarra_id? filters=min:1
  }

  stack {
    db.del codigobarra {
      field_name = "id"
      field_value = $input.codigobarra_id
    }
  }

  response = null
  guid = "slAvZfkKeTcGrDPoaKyVUqJGd4Q"
}