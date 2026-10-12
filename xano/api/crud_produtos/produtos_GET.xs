// Query all produtos records
query produtos verb=GET {
  api_group = "CRUD Produtos"

  input {
  }

  stack {
    db.query produtos {
      return = {type: "list"}
    } as $model
  }

  response = $model
  guid = "zAwDnKf4AaB_UB5boe7O1uewa1c"
}