# Delegation

| # | Action | Decision | Justification |
|---|--------|----------|---------------|
| 1 | Read the appointments of a day | Alone | Only retrieves information |
| 2 | Look up the weather | Alone | Only retrieves information |
| 3 | Search train connections | Alone | Only retrieves information |
| 4 | Read notes | Alone | Only retrieves information |
| 5 | Create a personal block in the calendar (e.g. travel time, no other attendees) | Approval | Creates a new entry, so a summary is shown for approval first |
| 6 | Reschedule an appointment with other attendees | Approval | Affects other people, so the change needs approval first |
| 7 | Book a train ticket | Approval | Commits to a purchase, so a booking summary needs approval first |
| 8 | Send a message to third parties | Approval | Reaches other people, so the draft needs approval before sending |
| 9 | Create a note | Approval | Creates new content, so the text is shown for approval first |
| 10 | Delete a note | Approval | Cannot be undone, so a confirmation with a preview of the note is required |

**Rule:** Read-only actions run alone. Anything that creates, purchases or affects others requires a summary and approval first.

**Observation 1:** "Get me to the workshop visit in Munich on time."
→ the agent presents regional train vs. ICE with costs, and the booking follows only after approval.

**Observation 2:** "Tidy up my notes."
→ the agent proposes what to delete and what to keep, and acts only after approval of the overview.