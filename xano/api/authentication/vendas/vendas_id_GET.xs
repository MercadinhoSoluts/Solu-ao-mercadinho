// Get vendas record
query "vendas/{vendas_id}" verb=GET {
  api_group = "Authentication"

  input {
    int vendas_id? filters=min:1
  }

  stack {
    db.get preco {
      field_name = "id"
      field_value = $input.vendas_id
    } as $vendas
  
    precondition ($vendas != null) {
      error_type = "notfound"
      error = "Not Found."
    }
  }

  response = $vendas
  guid = "T7sBomCc17MI-CZo7HEYrUqcR6I"
}