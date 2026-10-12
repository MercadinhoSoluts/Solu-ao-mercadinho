// Query all codigobarra records
query codigobarra verb=GET {
  api_group = "Authentication"

  input {
  }

  stack {
    db.query codigobarra {
      return = {type: "list"}
    } as $codigobarra
  }

  response = $codigobarra
  guid = "ynhtA3dFryDMl5QJWxpWITOm2Rg"
}