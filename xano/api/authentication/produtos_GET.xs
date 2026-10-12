// Query all produtos records
query produtos verb=GET {
  api_group = "Authentication"

  input {
  }

  stack {
    db.query produtos {
      return = {type: "list"}
    } as $produtos
  }

  response = $produtos
  guid = "rGhbyHL8V26BcHxnWMq3oEmYWvM"
}