// Update an employee account without exposing credentials.
query "users/{user_id}" verb=PATCH {
  api_group = "Authentication"
  auth = "user"

  input {
    int user_id? filters=min:1
    text name?
    email email? filters=trim|lower
    text password?
    enum role? {
      values = ["operator", "manager", "owner"]
    }
  }

  stack {
    db.get user {
      field_name = "id"
      field_value = $auth.id
      output = ["role", "is_active"]
    } as $requester

    precondition ($requester.role == "owner" || $requester.role == "manager") {
      error_type = "accessdenied"
      error = "You are not authorized to update employees."
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

    precondition ($requester.role == "owner" || $input.role == "operator") {
      error_type = "accessdenied"
      error = "Managers may only assign the operator role."
    }

    util.get_raw_input {
      encoding = "json"
      exclude_middleware = false
    } as $raw_input

    db.patch user {
      field_name = "id"
      field_value = $input.user_id
      data = `$input|pick:($raw_input|keys)|filter_null|filter_empty_text`
    } as $user
  }

  response = `$user|pick:["id","name","email","role","is_active"]`
  guid = "OHOGax5rkm-0qg3gyXoL6-A8Oow"
}
