// Get codigobarra record
query "codigobarra/{codigobarra_id}" verb=GET {
  api_group = "Authentication"

  input {
    int codigobarra_id? filters=min:1
  }

  stack {
    db.get codigobarra {
      field_name = "id"
      field_value = $input.codigobarra_id
    } as $codigobarra
  
    precondition ($codigobarra != null) {
      error_type = "notfound"
      error = "Not Found."
    }
  }

  response = $codigobarra
  guid = "dwvy-wecNuTuvYSwI-SK5LCSViQ"
}