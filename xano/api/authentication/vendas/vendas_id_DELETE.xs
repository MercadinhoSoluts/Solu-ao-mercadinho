// Delete vendas record.
query "vendas/{vendas_id}" verb=DELETE {
  api_group = "Authentication"

  input {
    int vendas_id? filters=min:1
  }

  stack {
    db.del preco {
      field_name = "id"
      field_value = $input.vendas_id
    }
  }

  response = null
  guid = "Y5KCqPaFmihLyigzheZWw09uiBU"
}