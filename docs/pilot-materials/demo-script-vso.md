# Benefits Navigator — VSO Demo Script

*Demo flow for Veterans Service Organization staff*

**Duration:** 15-20 minutes
**Audience:** VSO administrators, caseworkers, accredited representatives

---

## Pre-Demo Setup

1. Create demo organization in BN
2. Create 2-3 test cases with varying statuses
3. Have sample documents ready (decision letter, medical record)
4. Ensure test veteran account exists with shared documents

---

## Demo Flow

### Opening (2 min)

> "Benefits Navigator helps VSOs manage veteran cases more efficiently. Today I'll show you how BN can help you:
>
> 1. **Triage cases faster** — See which cases need attention at a glance
> 2. **Identify evidence gaps** — Know exactly what's missing before filing
> 3. **Collaborate with veterans** — Securely review their documents
> 4. **Track outcomes** — Measure your win rates and case throughput"

---

### Scene 1: Dashboard Overview (3 min)

**Navigate to:** `/vso/`

**Key points to highlight:**

1. **Case counts by status**
   > "Right here you can see your entire caseload at a glance — how many are in intake, gathering evidence, filed, or pending decision."

2. **Priority cases panel**
   > "These are the cases that need your attention first — either marked urgent or have overdue action dates."

3. **Your assigned cases**
   > "If you're a caseworker, you'll see your personal queue here."

4. **Win rate metrics**
   > "Track your outcomes — see how many cases you've won versus denied. This helps identify what's working."

5. **Stale cases alert**
   > "Cases with no activity in 30+ days show up here. No case falls through the cracks."

---

### Scene 2: Case List & Triage (3 min)

**Navigate to:** `/vso/cases/`

**Key points to highlight:**

1. **Filtering**
   > "Filter by status, priority, assigned caseworker, or triage label. Find exactly what you need."

2. **Triage labels** (if implemented)
   > "The triage column tells you at a glance:
   > - Green 'Ready to file' — all evidence in
   > - Yellow 'Needs evidence' — missing documentation
   > - Red 'Needs nexus' — no medical nexus established"

3. **Search**
   > "Search by veteran name, condition, or case notes."

4. **CSV export**
   > "Export your filtered results to CSV for reporting or your own systems."

---

### Scene 3: Case Detail Deep Dive (5 min)

**Navigate to:** `/vso/cases/<id>/`

**Key points to highlight:**

1. **Case header**
   > "All the key info at a glance — veteran name, status, priority, assigned caseworker, next action date."

2. **Conditions overview** (if implemented)
   > "Each claimed condition shows:
   > - Current and target rating
   > - Evidence gap status — diagnosis, in-service event, nexus
   > - Workflow status from identified to granted/denied"

3. **Shared documents**
   > "Veterans share documents with you through BN. You see them organized by type — medical records, decision letters, service records."

4. **AI analyses**
   > "When a veteran runs our AI tools, they can share the results with you. Decision letter breakdowns, evidence gap analyses — all here."

5. **Case notes**
   > "Add notes for your team. Mark action items. Set due dates. Everything tracked."

6. **Timeline**
   > "Full history of the case — when it was created, every status change, every note added."

---

### Scene 4: Document Review (3 min)

**Click on a shared document**

**Key points to highlight:**

1. **Secure viewing**
   > "Documents use time-limited signed URLs. Links expire after 30 minutes. No permanent download links floating around."

2. **Document metadata**
   > "See file type, upload date, and any AI-extracted summary — without exposing the raw medical text."

3. **Review status**
   > "Mark documents as reviewed. Track who reviewed what and when."

---

### Scene 5: Adding a Case Note (2 min)

**Add a note to a case**

**Key points to highlight:**

1. **Note content**
   > "Write your notes, tag action items, set due dates."

2. **Audit trail**
   > "Every note is timestamped with who wrote it. Full accountability."

3. **Read-only for archived cases**
   > "Once a case is closed and archived, it becomes read-only. No accidental changes to closed cases."

---

### Scene 6: Security & Compliance (2 min)

**Key points to highlight:**

1. **Organization isolation**
   > "You only see cases for your organization. Complete data isolation between VSOs."

2. **Audit logging**
   > "Every document view, download, case update — all logged. For compliance and accountability."

3. **No raw PHI storage**
   > "We never store raw medical record text. AI processes it, extracts insights, then the original is discarded."

4. **Consent-based sharing**
   > "Veterans control what they share. They grant access explicitly."

---

### Closing (2 min)

> "What we've seen:
>
> - **Dashboard** — instant visibility into your caseload
> - **Triage** — know which cases need attention
> - **Evidence gaps** — identify what's missing
> - **Collaboration** — securely work with veterans
> - **Accountability** — full audit trail
>
> Questions?"

---

## Common Questions

**Q: Can multiple caseworkers work on the same case?**
> "Yes. Cases can be reassigned, and anyone in your organization can view and add notes. The assigned caseworker is just the primary contact."

**Q: How do veterans share documents?**
> "Veterans upload to their own account, then click 'Share with VSO' and select your organization. You'll see it in the case automatically."

**Q: Can I import existing cases?**
> "We have a CSV import feature planned. For the pilot, cases are created manually or by veterans when they connect."

**Q: What if a veteran works with multiple VSOs?**
> "Veterans can share with multiple organizations. Each VSO sees only what's shared with them."

**Q: How much does it cost?**
> "Pilot pricing: $XX/seat/month or $XX/org/month. We're validating pricing during the pilot."

---

## Demo Environment URLs

- Dashboard: `/vso/`
- Case list: `/vso/cases/`
- Create case: `/vso/cases/new/`
- Invitations: `/vso/invitations/`

---

*Script version: 1.0*
*Last updated: January 2025*
