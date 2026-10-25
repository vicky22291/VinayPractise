#!/usr/bin/env bash
# Smoke test of every Q&A API against a running server: ./curl.sh, or BASE=http://host:port ./curl.sh.
# Each step prints the request and its status, the Location, Allow and Idempotent-Replayed headers when present, and
# the body. A status other than the expected one is flagged, and the script then exits 1.
set -u
BASE=${BASE:-http://localhost:8080}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
FAILURES=0
JSON='Content-Type: application/json'

# step TITLE: prints a heading for the next request.
step() {
  echo
  echo "== $*"
}

# call EXPECTED_STATUS METHOD PATH [curl args...]: sends one request and prints the result. The body stays in
# $TMP/body for field.
call() {
  local expected=$1 method=$2 path=$3
  shift 3
  rm -f "$TMP/headers" "$TMP/body"
  local status
  status=$(curl -s -X "$method" "$BASE$path" -D "$TMP/headers" -o "$TMP/body" -w '%{http_code}' "$@")
  if [ "$status" = "$expected" ]; then
    echo "$method $path -> $status"
  else
    echo "$method $path -> $status, expected $expected  <-- UNEXPECTED"
    FAILURES=$((FAILURES + 1))
  fi
  grep -iE '^(Location|Allow|Idempotent-Replayed):' "$TMP/headers" 2>/dev/null | tr -d '\r'
  cat "$TMP/body" 2>/dev/null
  echo
}

# field NAME: prints a top-level string field of the last body, or nothing when it's null. Uses jq when it's installed.
# Otherwise grep and cut, which is enough here: every question or answer body starts with its own "id", and only a list
# page has a "nextCursor", so the first match is the top-level one.
field() {
  if command -v jq >/dev/null 2>&1; then
    jq -r --arg name "$1" '.[$name] // empty' "$TMP/body" 2>/dev/null
  else
    grep -o "\"$1\":\"[^\"]*\"" "$TMP/body" 2>/dev/null | head -n 1 | cut -d '"' -f 4
  fi
}

QUESTION='{"content": "How do I make a ConcurrentHashMap value update atomic?", "tags": ["Java", "concurrency", "java"]}'
QUESTION_EDIT='{"content": "How do I make it atomic without locks?", "tags": ["java", "ConcurrentHashMap"]}'
QUESTION_2='{"content": "When does ConcurrentHashMap.values() see a concurrent put?", "tags": ["java"]}'
ANSWER='{"content": "Use compute() or merge(). Both run atomically per key."}'
ANSWER_EDIT='{"content": "Use compute() or merge(). Both run atomically per key, so no explicit lock is needed."}'

# The server is up.
step "Health check"
call 200 GET /health

# 1. alice asks. The tags come back lowercased and deduplicated. Every write needs its own Idempotency-Key.
step "1. alice creates a question with tags"
CREATE_KEY=$(uuidgen)
call 201 POST /questions -H "X-User-Id: alice" -H "Idempotency-Key: $CREATE_KEY" -H "$JSON" -d "$QUESTION"
QID=$(field id)
if [ -z "$QID" ]; then
  echo "No question id in the response. Is the server running at $BASE?"
  exit 1
fi

# 2. Reads are public, so there's no X-User-Id.
step "2. Anyone gets the question"
call 200 GET "/questions/$QID"

# 3. A retry with the same user and key gets the original 201 back instead of a second question.
step "3. alice retries the create with the same key: a replay"
call 201 POST /questions -H "X-User-Id: alice" -H "Idempotency-Key: $CREATE_KEY" -H "$JSON" -d "$QUESTION"

# 4. PUT replaces content and tags, and sets updatedAt.
step "4. alice, the author, updates the question"
call 200 PUT "/questions/$QID" -H "X-User-Id: alice" -H "Idempotency-Key: $(uuidgen)" -H "$JSON" -d "$QUESTION_EDIT"

# 5. Only the author may edit a question.
step "5. mallory tries to update it: 403 NOT_QUESTION_OWNER"
call 403 PUT "/questions/$QID" -H "X-User-Id: mallory" -H "Idempotency-Key: $(uuidgen)" -H "$JSON" -d "$QUESTION_EDIT"

# 6. bob answers. The Location points to the new answer.
step "6. bob answers the question"
call 201 POST "/questions/$QID/answers" -H "X-User-Id: bob" -H "Idempotency-Key: $(uuidgen)" -H "$JSON" -d "$ANSWER"
AID=$(field id)

# 7. Answers are public too.
step "7. Anyone gets the answer"
call 200 GET "/questions/$QID/answers/$AID"

# 8. Only the answer's author may edit it.
step "8. bob updates his answer"
call 200 PUT "/questions/$QID/answers/$AID" -H "X-User-Id: bob" -H "Idempotency-Key: $(uuidgen)" -H "$JSON" \
  -d "$ANSWER_EDIT"

# 9. One answer per user per question. The message names the answer to update instead.
step "9. bob answers again under a new key: 409 ANSWER_ALREADY_EXISTS"
call 409 POST "/questions/$QID/answers" -H "X-User-Id: bob" -H "Idempotency-Key: $(uuidgen)" -H "$JSON" -d "$ANSWER"

# 10. Votes have no body. The response is the question's count, including this vote.
step "10. bob upvotes alice's question"
call 201 POST "/questions/$QID/upvotes" -H "X-User-Id: bob" -H "Idempotency-Key: $(uuidgen)"

# 11. Nobody can upvote what they wrote.
step "11. alice tries to upvote her own question: 403 CANNOT_UPVOTE_OWN"
call 403 POST "/questions/$QID/upvotes" -H "X-User-Id: alice" -H "Idempotency-Key: $(uuidgen)"

# 12. One vote per user. A retry with the first key would replay the 201 instead.
step "12. bob upvotes it again under a new key: 409 ALREADY_UPVOTED"
call 409 POST "/questions/$QID/upvotes" -H "X-User-Id: bob" -H "Idempotency-Key: $(uuidgen)"

# 13. The question's author may upvote other users' answers.
step "13. alice upvotes bob's answer"
call 201 POST "/questions/$QID/answers/$AID/upvotes" -H "X-User-Id: alice" -H "Idempotency-Key: $(uuidgen)"

# 14. Downvotes are counted apart from upvotes. The response is the answer's downvote count.
step "14. carol downvotes bob's answer"
call 201 POST "/questions/$QID/answers/$AID/downvotes" -H "X-User-Id: carol" -H "Idempotency-Key: $(uuidgen)"

# 15. Nobody can downvote what they wrote either.
step "15. bob tries to downvote his own answer: 403 CANNOT_DOWNVOTE_OWN"
call 403 POST "/questions/$QID/answers/$AID/downvotes" -H "X-User-Id: bob" -H "Idempotency-Key: $(uuidgen)"

# 16. One vote per user per target, up or down. The 409 names the vote already held.
step "16. bob, who upvoted the question, downvotes it: 409 ALREADY_UPVOTED"
call 409 POST "/questions/$QID/downvotes" -H "X-User-Id: bob" -H "Idempotency-Key: $(uuidgen)"

# 17. Every question and answer body carries both counts.
step "17. Anyone gets the question: upvotes 1, downvotes 0 on the question; upvotes 1, downvotes 1 on the answer"
call 200 GET "/questions/$QID"

# 18. A second java question, so the java list below has more than one page.
step "18. dave creates another question tagged java"
call 201 POST /questions -H "X-User-Id: dave" -H "Idempotency-Key: $(uuidgen)" -H "$JSON" -d "$QUESTION_2"

# 19. Lists are public too. Newest first, 20 per page by default. Items carry answerCount instead of the answers.
step "19. Anyone lists every question: dave's first, then alice's"
call 200 GET /questions

# 20. One per page. Tags match in any case; c# or c++ would be sent URL-encoded (c%23, c%2B%2B).
step "20. Anyone lists java questions one per page: dave's, with a nextCursor"
call 200 GET "/questions?tag=java&limit=1"
CURSOR=$(field nextCursor)
if [ -z "$CURSOR" ]; then
  echo "No nextCursor in the response  <-- UNEXPECTED"
  FAILURES=$((FAILURES + 1))
fi

# 21. The client sends nextCursor back as after. On a fresh server this is the last page, so nextCursor is null.
step "21. Anyone gets the next java page after that nextCursor: alice's"
call 200 GET "/questions?tag=java&limit=1&after=$CURSOR"

# 22. Bad input never reaches the service. The message lists every violation.
step "22. alice sends blank content and a tag with a space: 400 VALIDATION_FAILED"
call 400 POST /questions -H "X-User-Id: alice" -H "Idempotency-Key: $(uuidgen)" -H "$JSON" \
  -d '{"content": "   ", "tags": ["spring boot"]}'

echo
if [ "$FAILURES" -eq 0 ]; then
  echo "Every step returned the expected status."
else
  echo "$FAILURES step(s) returned an unexpected status."
  exit 1
fi
