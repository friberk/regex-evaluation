# Survey — Instrument and Responses

This folder contains the user study materials and anonymized responses referenced in the paper. The survey probed engineers’ preferences about variance in candidate regex sets (strictness and related non‑functional properties) to support our interpretation of results.

## Files
- `anonymized_survey_instrument.pdf` — final instrument shown to participants (consent, screening, tasks, and questions about candidate‑set variance).
- `anonymized_survey_responses.xlsx` — anonymized responses that passed screening and consistency checks (no PII).

## Study summary
- Oversight: IRB‑approved; participants consented.
- Recruitment: Prolific; inclusion criteria required software/IT roles and regex familiarity.
- Cohort: 38 total responses; 32 passed screening and were analyzed.
- Task format: 4 composition tasks (popular RegExLib patterns). For each, participants chose a preferred regex, then selected which of two candidate sets (high‑ vs low‑variance) they would find more useful, and reflected on whether seeing the sets changed their preference.
- Key finding: most participants reported that seeing a range of strictness (higher variance) helped selection.

## Using the responses
- Load with Python/pandas:
  ```python
  import pandas as pd
  df = pd.read_excel('survey/anonymized_survey_responses.xlsx')
  print(df.head())
  ```
- The workbook includes anonymized selections and Likert‑style answers; IDs are synthetic and not linkable to PII.
