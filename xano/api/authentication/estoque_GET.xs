// Query all estoque records
query estoque verb=GET {
  api_group = "Authentication"

  input {
  }

  stack {
    db.query estoque {
      return = {type: "list"}
    } as $estoque
  }

  response = $estoque
  guid = "vyNCVOpGZSDwACllhb1hdljWQtw"
}