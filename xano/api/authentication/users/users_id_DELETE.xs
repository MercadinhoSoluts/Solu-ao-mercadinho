// Delete an employee account after server-side authorization.
query "users/{user_id}" verb=DELETE {
  api_group = "Authentication"
  auth = "user"

  input {
    int user_id? filters=min:1
  }

  stack {
    db.get user {
      field_name = "id"
      field_value = $auth.id
      output = ["role", "is_active"]
    } as $requester

    precondition ($requester.role == "owner" || $requester.role == "manager") {
      error_type = "accessdenied"
      error = "You are not authorized to delete employees."
    }

    precondition ($input.user_id != $auth.id) {
      error_type = "accessdenied"
      error = "You cannot delete your own account."
    }

    db.get user {
      field_name = "id"
      field_value = $input.user_id
      output = ["id", "role"]
    } as $target

    precondition ($target != null) {
      error_type = "notfound"
      error = "Employee not found."
    }

    precondition ($requester.role == "owner" || $target.role == "operator") {
      error_type = "accessdenied"
      error = "Managers may only delete operator accounts."
    }

    db.del user {
      field_name = "id"
      field_value = $input.user_id
    }
  }

  response = null
  guid = "U2uvQoVsI646X6fjiY9W1GnbYDA"
}
