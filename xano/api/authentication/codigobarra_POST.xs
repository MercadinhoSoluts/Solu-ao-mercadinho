// Add codigobarra record
query codigobarra verb=POST {
  api_group = "Authentication"

  input {
    dblink {
      table = "codigobarra"
    }
  }

  stack {
    db.add codigobarra {
      enforce_hidden_fields = false
      data = {created_at: "now"}
    } as $codigobarra
  }

  response = $codigobarra
  guid = "Vk0i55S7Wshrwi5Ird8JMrbvpM8"
}