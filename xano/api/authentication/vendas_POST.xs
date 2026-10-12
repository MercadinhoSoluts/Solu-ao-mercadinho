// Add vendas record
query vendas verb=POST {
  api_group = "Authentication"

  input {
    dblink {
      table = "preco"
    }
  }

  stack {
    db.add preco {
      enforce_hidden_fields = false
      data = {created_at: "now"}
    } as $vendas
  }

  response = $vendas
  guid = "2BQ7U0CFcTna6jg2ZHKWOyCmr0s"
}