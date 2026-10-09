# scoping-drills/ conventions

Requirements-scoping practice: 10-minute sprints against a hidden card, run in the Claude desktop voice agent. The root `CLAUDE.md` still applies.

- **Never show the user anything from `cards.md`.** That includes card content, the crux, constraints, or hints. The cards only work as a surprise. Edit them without quoting them back.
- `README.md` is the user-facing file: rules, opening script, Stripe numbers, scorecard, log, and the prompt one-liners. The prompt one-liners are safe to show.
- New cards follow the existing card format in `cards.md`: Say, Source, Product context, 3 hidden constraints each with a trigger, Crux, Good cuts, Wrong cut, Numbers. Add every new card to one mode list (Stripe or Ambiguity) in `cards.md` §0.1, and to the prompt table in `README.md` §9 in the same order. The two orders must match.
- Exclude any prompt whose solution already exists in `hld/`. Studied prompts go in the speed-rep list (`README.md` §10) instead, with the `hld/` folder as the card.
- Log rows go in `README.md` §8. When the user pastes rows from the voice agent, append them there.
