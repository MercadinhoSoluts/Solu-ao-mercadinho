addon user {
  input {
    int user_id? {
      table = "user"
    }
  }

  stack {
    db.query user {
      where = $db.user.id == $input.user_id
      return = {type: "single"}
    }
  }

  guid = "s7UHnf7WtH4oKKdWUGGOyQGbS8E"
}