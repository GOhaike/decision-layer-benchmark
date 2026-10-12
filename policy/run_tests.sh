#!/usr/bin/env sh
# Runs the six refund cases against refunds.rego and checks each result.
# Needs OPA on PATH: https://www.openpolicyagent.org/docs/latest/#running-opa
set -e
cd "$(dirname "$0")"
fail=0
check() {
  got=$(opa eval -f raw -d refunds.rego -i "tests/$1" data.refunds.allow)
  if [ "$got" = "$2" ]; then echo "pass  $1  allow=$got"; else echo "FAIL  $1  allow=$got, expected $2"; fail=1; fi
}
check 1_attack.json false
check 2_clean.json true
check 3_fooled_newcard.json false
check 4_fooled_notowner.json false
check 5_fooled_amount.json false
check 6_fooled_cardmissing.json false
exit $fail
