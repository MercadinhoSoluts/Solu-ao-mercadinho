// Query all vendas records
query vendas verb=GET {
  api_group = "Authentication"

  input {
  }

  stack {
    db.query preco {
      return = {type: "list"}
    } as $vendas
  }

  response = $vendas
  guid = "Y8VTqW0u2HvpjK0IAl45fviDfc8"
}