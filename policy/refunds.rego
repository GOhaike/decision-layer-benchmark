package refunds

default allow := false
allow if {
    input.order.owner == input.user.id          # system of record
    input.order.amount <= 500                   # system of record
    input.account.card_added_last_24h == false  # system of record
    input.facts.intent == "refund"              # Jev
    input.facts.injection < 0.2                 # Jev, blocks only
}
