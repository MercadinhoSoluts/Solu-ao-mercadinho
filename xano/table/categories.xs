table categories {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    text name
    bool is_active?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "name"}]}
  ]

  guid = "AIEuhgxv-SipUtPEEyJ6vsH6ffw"
}