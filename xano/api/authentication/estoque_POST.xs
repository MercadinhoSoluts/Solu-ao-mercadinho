// Add estoque record
query estoque verb=POST {
  api_group = "Authentication"

  input {
    dblink {
      table = "estoque"
    }
  }

  stack {
    db.add estoque {
      enforce_hidden_fields = false
      data = {created_at: "now"}
    } as $estoque
  }

  response = $estoque
  guid = "Seq1LwrphUMdtwYrtFuJcQ4FeXA"
}