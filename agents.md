# GameGrid agent rules

## Published puzzle immutability

- Treat every puzzle dated today or earlier as published and immutable.
- Ordinary UI, logic, criteria and catalogue changes must apply only to future-dated puzzles.
- Do not regenerate, backfill, renumber or otherwise alter a published puzzle, including its clues, valid answers, difficulty or mode name, unless Harry explicitly asks for that specific historical change or a full schedule reset.
- Before changing puzzle-generation behaviour, preserve the existing published schedule and verify that only dates after today can change.
- Page-only updates must reuse the current published catalogue rather than rebuild it.
