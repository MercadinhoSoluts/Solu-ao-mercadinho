// Get produtos record
query "produtos/{produtos_id}" verb=GET {
  api_group = "Authentication"

  input {
    int produtos_id? filters=min:1
  }

  stack {
    db.get produtos {
      field_name = "id"
      field_value = $input.produtos_id
    } as $produtos
  
    precondition ($produtos != null) {
      error_type = "notfound"
      error = "Not Found."
    }
  }

  response = $produtos
  guid = "HvDCiO8xhZI-bvXfXsLYggftiTw"
}