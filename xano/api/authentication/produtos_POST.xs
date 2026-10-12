// Add produtos record
query produtos verb=POST {
  api_group = "Authentication"

  input {
    dblink {
      table = "produtos"
    }
  }

  stack {
    db.add produtos {
      enforce_hidden_fields = false
      data = {created_at: "now"}
    } as $produtos
  }

  response = $produtos
  guid = "7NUK707OcY2EVZguAVCTnPJ_I_U"
}