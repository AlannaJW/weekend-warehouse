# 01 — Scoping

This is the prompt I used to nail down the project shape before any code
was written. The key move was constraining scope hard (one weekend, ~10
hours, demonstration-not-production) so the AI's suggestions stayed
realistic rather than ballooning to a full enterprise warehouse.

---

> I want to brush up on analytical databases. I know their purposes
> compared to relational databases, but want more examples of the kinds
> of summaries, aggregations, and uses that ETL would do for a database
> warehouse.

> Can you take this same information and walk me through a singular
> example with multiple databases and one data warehouse with typical
> ETL processes

> A lot of what I want to communicate is that I understand what is
> happening, but know how to utilize AI to complete a project — the job
> is very AI heavy and they need someone who can onboard quickly and use
> AI to save as much time as possible. How can the project change
> accordingly and how can you help me complete it

> My timeline is closer to 1 weekend, 2 days, 10ish hours, and doesn't
> have to be grand by any means, just enough to show that I know how it
> works and how AI works with it

> I would rather you Big Query and Looker Studio, but other than that, I
> like this plan.

---

## What I was doing

I started by *learning the domain*, not by asking for a project. The first
two prompts above are actually about analytical databases as a concept.
That matters because by the time I asked for a project, I could push back
on suggestions that didn't fit my goals.

The third prompt reframes the whole project around AI fluency, which
changes both the scope (smaller, more documented) and the framing
(workflow is the artifact, not just the code).

The fourth and fifth narrow scope and stack to fit a real timeline.

## What I would have done differently

Skipped Snowflake from the option set. We never seriously considered it
once BigQuery's free tier was on the table, so it cluttered the decision.
