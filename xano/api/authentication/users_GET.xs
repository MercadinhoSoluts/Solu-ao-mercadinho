// List employee accounts without credential fields.
query users verb=GET {
  api_group = "Authentication"
  auth = "user"

  input {
    text search?
  }

  stack {
    db.get user {
      field_name = "id"
      field_value = $auth.id
      output = ["role", "is_active"]
    } as $requester

    precondition ($requester.role == "owner" || $requester.role == "manager") {
      error_type = "accessdenied"
      error = "You are not authorized to list employees."
    }

    db.query user {
      where = $db.user.is_active == true
      return = {type: "list"}
      output = ["id", "name", "email", "role", "is_active"]
    } as $users
  }

  response = $users
  guid = "7EtyCunwlEYDCBz_d8l4b8ieqCU"
}
