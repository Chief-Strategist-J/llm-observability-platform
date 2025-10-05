In fast-moving marketing, speed matters — but control matters even more.
This pipeline is designed to give you both: **daily LinkedIn posts and 20 evenly spaced tweets**, all driven by **AI or manual input**, yet guarded by **strict two-step approvals**. With Slack as the control center, Google Sheets as the knowledge base, and n8n as the orchestrator, you can generate, review, confirm, and schedule content without ever risking an accidental post.

---


# 🧭 High-Level: Two Workflows

* **Workflow A — Orchestrator (Daily LI + TW approvals & scheduling)**
  Runs once daily, collects/creates content, gets your approvals, posts LinkedIn, and **queues** tweets.

* **Workflow B — Tweet Poster (every 10 min)**
  Picks up **due** tweets from the queue and posts them (evenly spaced, restart-safe).

---

# 📋 ASCII Decision Flow (Strict, with Sheet topic & double confirm)

```
[Trigger A: Cron 09:00]
    |
    v
[LINKEDIN STAGE]
 ├─ Slack: "LinkedIn → AI ✨ or Manual ✍️?"
 └─ Slack Trigger (choice)
      |
      +─ Manual ✍️
      |    ├─ Slack Trigger: "Type LinkedIn post"
      |    ├─ Slack Preview → Approve? [Yes/No]
      |    |     ├─ No → ask again
      |    |     └─ Yes → Slack: "Are you sure?" → Confirm ✅ → LinkedIn Post
      |    └─ Log LI outcome
      |
      └─ AI ✨
           ├─ Google Sheets: lookup today’s topic
           |     ├─ Found → use it
           |     └─ Not found → Slack: "Send today’s topic" → Slack Trigger
           ├─ AI (HTTP): generate LI draft
           ├─ Slack Preview → Approve? [Yes/No]
           |     ├─ No → Slack: "Retry AI or Switch to Manual?"
           |     |        ├─ Retry AI → regenerate → preview…
           |     |        └─ Manual → capture text → preview → post
           |     └─ Yes → Slack: "Are you sure?" → Confirm ✅ → LinkedIn Post
           └─ Log LI outcome
    |
    v
[TWITTER STAGE]
 ├─ Slack: "Twitter → AI ✨ or Manual ✍️?"
 └─ Slack Trigger (choice)
      |
      +─ Manual ✍️
      |    ├─ Slack: "Send 20 tweets, one message at a time"
      |    ├─ Slack Trigger (collect messages) → Collector stores array
      |    |     ├─ count < 20 → keep waiting
      |    |     └─ count = 20 → proceed
      |    ├─ Slack Preview (1–20) → Approve? [Yes/No]
      |    |     ├─ No → clear array → restart collection
      |    |     └─ Yes → Slack: "Are you sure?" → Confirm ✅
      |    ├─ Create Tweet Queue rows (20) with hourly spacing + jitter
      |    └─ Log queue creation
      |
      └─ AI ✨
           ├─ Google Sheets: lookup today’s topic
           |     ├─ Found → use it
           |     └─ Not found → Slack: "Send today’s topic" → Slack Trigger
           ├─ AI (HTTP): generate 20 tweets
           ├─ Slack Preview (numbered) → Approve? [Yes/No]
           |     ├─ No → "Retry AI or Switch to Manual?"
           |     |        ├─ Retry AI → regenerate → preview…
           |     |        └─ Manual → 20 msg collection path
           |     └─ Yes → Slack: "Are you sure?" → Confirm ✅
           ├─ Create Tweet Queue rows (20) with hourly spacing + jitter
           └─ Log queue creation
    |
    v
[Slack notify: "✅ LinkedIn posted / ✅ Tweets scheduled"]
[Sheets: Append run logs]

----------------------------------------------

[Trigger B: Cron every 10 min]
    |
    v
[Tweet Poster]
 ├─ Sheets: read queue where status=pending AND scheduled_at<=now
 ├─ For each due item:
 |     ├─ Idempotency check (content hash / not posted today)
 |     ├─ Post via Twitter Node
 |     ├─ Update row → status=posted, tweet_id, posted_at
 |     └─ On error: status=failed, error, retry_count++, Slack alert
 └─ Slack summary on failures (button: "Retry now")
```

---
## 🏁 Conclusion

This workflow delivers **automation with safeguards**: you save time through AI generation and tweet scheduling, while never losing editorial control. By enforcing **explicit approvals, reconfirmation, and robust queuing**, the system guarantees that nothing goes live unless you want it to — and once approved, it runs reliably even across restarts. In short, it’s a **bulletproof marketing automation pipeline**: efficient, scalable, and safe.

---
