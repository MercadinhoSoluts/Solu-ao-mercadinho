// Delete estoque record.
query "estoque/{estoque_id}" verb=DELETE {
  api_group = "Authentication"

  input {
    int estoque_id? filters=min:1
  }

  stack {
    db.del estoque {
      field_name = "id"
      field_value = $input.estoque_id
    }
  }

  response = null
  guid = "b8N0-ZcNnEHXXWJ-6_diugSCFsI"
}