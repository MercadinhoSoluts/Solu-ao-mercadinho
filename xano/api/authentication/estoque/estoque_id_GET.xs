// Get estoque record
query "estoque/{estoque_id}" verb=GET {
  api_group = "Authentication"

  input {
    int estoque_id? filters=min:1
  }

  stack {
    db.get estoque {
      field_name = "id"
      field_value = $input.estoque_id
    } as $estoque
  
    precondition ($estoque != null) {
      error_type = "notfound"
      error = "Not Found."
    }
  }

  response = $estoque
  guid = "0Zr8-zkq3LTqrRhxPuFxMt_4IZU"
}