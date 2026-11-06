# Interviewer: reveal one stage at a time

## Stage 2: Boolean expressions

Add true/false literals and AND/OR, case-sensitive, with AND taking precedence over OR. Keywords inside quoted values are string content. Keep string equality behavior.

## Stage 3: Parentheses and invalid input

Add parentheses. Give a useful error for invalid syntax rather than silently choosing an action. State how null values and type mismatches behave.

## Discussion

How do you distinguish tokenization from evaluation? Where would you cache parsed rules? How do you safely roll out a changed ruleset and explain why a transaction was blocked?
