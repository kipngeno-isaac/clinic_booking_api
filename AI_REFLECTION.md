# AI Reflection

## 1. What did you use AI for across the four sections?

Mostly Sections 2 and 3, in a later pass over a system that already worked. I used Claude Code to:

- Keep the README accurate as I changed the infrastructure. For example, I moved the API behind nginx (binding it to 127.0.0.1:8000 instead of exposing the port directly), added the live docs URL, and removed an old "confirm the firewall allows inbound 8000" step that was no longer true once the port was private.
- Confirm the deployed app was actually reachable by hitting the live `/health` endpoint, instead of assuming a green pipeline meant it was up.
- Draft the compare-URL and PR title/body when `gh` wasn't installed and I had no token in the environment.
- Cross-check my code against the original assessment PDF. This is how I found that the required `reschedule` endpoint was missing, and then built it: the schema, a shared `_validate_slot` helper pulled out of `book_appointment`, the service function, the endpoint, and 8 new tests.

I also used it to draft the structure of this file, which I'm now filling in myself.

## 2. Give one example where an AI suggestion improved your work. What did you prompt it with?

Prompt: *"check against the pdf if we checked all the requirements"*.

It compared the assessment's required endpoints against the actual router, instead of trusting what the README claimed. It found that `PATCH /appointments/{id}/reschedule` — a required endpoint — didn't exist anywhere in the code. I had built approve/reject instead, which aren't in the spec at all, and my README table had been quietly wrong about that. It also caught that this reflection file didn't exist yet. Both were real gaps against the graded rubric, and they were easy to miss because the rest of the API looked finished.

## 3. Give one example where AI output was wrong or incomplete and how you caught it.

My README had a table of "endpoints from the original spec" that listed `approve` and `reject` as required. That was wrong — neither is in the actual assessment. It was AI-written content from an earlier pass, and I didn't catch it until I asked the AI to check the code against the source PDF directly, rather than against its own earlier summary of the spec. That's when both the mislabeling and the missing reschedule endpoint came out.

The lesson for me: an AI-maintained README describing "the spec" is only as reliable as the last time it was checked against the real source. I shouldn't treat it as ground truth on its own.

## 4. Name two decisions you made without AI. Why did you trust your own judgment there?

**Choosing FastAPI.** The brief let me pick FastAPI, Django REST, or Go, and I chose FastAPI. It's a Python framework, so it's easy for me to understand and reason about, and it's fast. It also comes with Swagger built in, which gives an interactive docs page on the web — that made it easy to test the API in the browser and meant the deployed URL wasn't just a bare endpoint. I trusted this decision because it was mine to weigh: I picked the framework that made the app easiest to test and verify, not just the one I was most used to.

**Keeping the reviewer notes out of my prep.** When it read the assessment PDF, it also picked up pages 7-12 — internal reviewer notes marked "not shared with candidates," including the planted bugs for the live code review and the answer key for the debugging exercise. It flagged this itself and didn't use those pages. I held the same line. I'd rather walk into the live session cold and be judged honestly than show up with answers I didn't actually reason through.