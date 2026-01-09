# Content Creation Prompts for Phase 3

## Overview

Use these prompts with your research session (Claude with web access) to generate content for:
1. **Glossary Terms** (20-30 core VA terms)
2. **General C&P Exam Guide** (accessible to all conditions)
3. **Condition-Specific Guides** (PTSD, Musculoskeletal, Tinnitus)

Each prompt is designed to produce content that matches your database schema and accessibility standards.

---

## Prompt 1: VA Terminology Glossary (20-30 Terms)

### Copy This Prompt:

```
I'm building a VA benefits navigation platform and need plain-language definitions for 30 core VA terminology terms that veterans struggle with.

For each term, provide:
1. **Term** (the official VA term)
2. **Plain Language** (simple 1-2 sentence explanation, 8th grade reading level)
3. **Context** (why this matters for veterans, when they'll encounter it)
4. **Example** (optional but helpful - a real scenario)

Terms to define:
- Service Connection
- Nexus Letter
- DBQ (Disability Benefits Questionnaire)
- Effective Date
- Presumptive Condition
- C&P Exam
- Range of Motion (ROM)
- Functional Limitation
- Flare-up
- ITF (Intent to File)
- Development (claims context)
- Duty to Assist
- VSO (Veterans Service Organization)
- VA Rating
- Combined Rating
- Bilateral Factor
- Service Treatment Records (STR)
- Lay Evidence
- Buddy Statement
- Nexus
- Direct Service Connection
- Secondary Service Connection
- Aggravation
- VA Form 21-526EZ
- VA Form 20-0995 (Supplemental Claim)
- VA Form 20-0996 (Higher-Level Review)
- VA Form 10182 (Notice of Disagreement)
- BVA (Board of Veterans' Appeals)
- Remand
- Fully Developed Claim (FDC)

Format each term like this:

**Service Connection**
Plain Language: Proving your disability is directly linked to something that happened during your military service.
Context: This is THE foundation of any VA disability claim. Without establishing service connection, you cannot receive disability compensation.
Example: If you injured your back lifting equipment in basic training, that back pain is "service-connected" because it happened during military service.

Use current 2025/2026 VA guidance and cite sources if possible.
```

---

## Prompt 2: General C&P Exam Preparation Guide

### Copy This Prompt:

```
I need to write a comprehensive, accessible guide for veterans preparing for ANY C&P (Compensation & Pension) exam. This guide will be displayed on a web page with 8 structured sections.

Key Requirements:
- 8th grade reading level (Flesch-Kincaid)
- Plain language (no unexplained jargon)
- Action-oriented (tell veterans what to DO)
- Reassuring but realistic tone
- 1,500-2,000 words total

Please write content for these 8 sections:

### 1. Introduction
- What is a C&P exam? (plain language)
- Who conducts them? (93% contractors, not VA employees)
- How long do they take? (15-30 minutes typically)
- Why they matter (exam determines rating)

### 2. What the Exam Measures
- DBQ forms (standardized questionnaires)
- Examiner fills out form, doesn't make final decision
- What rating specialists look for
- Connection to your specific condition

### 3. Physical Tests (if applicable)
- General overview (specific tests covered in condition guides)
- Range of motion measurements
- Functional assessments
- Pain is important to communicate

### 4. Questions to Expect
- Medical history questions
- Symptom frequency and severity
- Impact on work and daily life
- Treatment history
- Sample questions

### 5. Preparation Tips (Pre-Exam)
- Review your claim file and service records
- Find and read the DBQ form for your condition
- Write down symptoms with frequency/severity
- Document worst days, not just current moment
- Bring written notes and medication list
- Arrive 15 minutes early

### 6. Day-of Guidance
- Critical DON'Ts:
  - Don't take extra pain medication (masks symptoms)
  - Don't push through pain during tests
  - Don't assume examiner reviewed your file
  - Don't downplay symptoms
  - Don't exaggerate (hurts credibility)
- Critical DOs:
  - Describe worst days
  - Give specific examples
  - Explain functional limitations
  - Be honest and consistent

### 7. Common Mistakes
- Minimizing symptoms (military culture to "push through")
- Allowing ROM manipulation past pain point
- Not explaining full impact on daily life
- Assuming examiner knows your history
- Not bringing documentation

### 8. After the Exam
- Document what happened immediately
- Request exam results (how to get them)
- Challenge inadequate exam BEFORE rating decision
- What to do if exam felt rushed or incomplete
- Timeline for rating decision

Use current 2025/2026 VA exam procedures. Cite sources where helpful.
```

---

## Prompt 3: PTSD C&P Exam Guide (Priority 1)

### Copy This Prompt:

```
I need a detailed, veteran-friendly guide for preparing for a PTSD C&P exam. This is the #1 most claimed mental health condition and has the highest denial rate.

Key Requirements:
- 8th grade reading level
- Trauma-informed language (sensitive, not triggering)
- Practical, actionable guidance
- 1,500-2,000 words

Please write content for these 8 sections:

### 1. Introduction
- What makes PTSD exams different
- Mental health stigma acknowledgment
- What this exam determines
- Reassurance (it's okay to not be okay)

### 2. What the Exam Measures
- PTSD DBQ form breakdown (what examiner is documenting)
- Diagnostic criteria (DSM-5)
- Frequency and severity of symptoms
- Occupational and social impairment levels
- Rating levels (0%, 10%, 30%, 50%, 70%, 100%)

### 3. Physical Tests
- No physical tests, but may assess:
  - Appearance and demeanor
  - Affect and mood
  - Thought processes
  - Memory and concentration

### 4. Questions to Expect
- Trauma details (stressor event)
- Symptom questions:
  - Nightmares/flashbacks frequency
  - Avoidance behaviors
  - Hypervigilance
  - Sleep disturbances
  - Relationship impacts
- Suicidal ideation (this is standard, not alarm)
- Work history and social functioning

### 5. Preparation Tips
- Write down all PTSD symptoms before exam
- Document frequency (daily, weekly, monthly)
- Prepare specific examples of episodes
- Explain impact on work, relationships, daily tasks
- Consider bringing support person (spouse, friend)
- Review your service records for stressor validation
- Prepare buddy statements if available

### 6. Day-of Guidance
- It's okay to be emotional
- Answer honestly (don't minimize OR exaggerate)
- Describe worst days, not just today
- If you don't remember, say so
- Take breaks if needed
- Specific communication examples:
  - "I have nightmares 4-5 times per week"
  - "I avoid crowds because I get anxious"
  - "I haven't worked in 2 years because of panic attacks"

### 7. Common Mistakes
- Downplaying symptoms (trying to appear "strong")
- Not mentioning all symptoms (shame/stigma)
- Not explaining full impact on relationships/work
- Forgetting to mention medication side effects
- Not preparing specific examples
- Assuming examiner understands military culture

### 8. After the Exam
- Write down everything immediately
- Document if exam felt inadequate
- How to challenge insufficient mental health exam
- What to do if examiner didn't review file
- Timeline for results

Include a checklist of 10-15 tasks for PTSD exam prep that I can add to the database as JSON:

```json
[
  {"id": "task-1", "task": "Find and read PTSD DBQ form (VA Form 21-0960P-2)", "timing": "2 weeks before"},
  ... (create 10-15 tasks)
]
```

Use current VA PTSD exam procedures and DBQ forms (2025/2026).
```

---

## Prompt 4: Musculoskeletal C&P Exam Guide (Priority 2)

### Copy This Prompt:

```
I need a detailed guide for preparing for musculoskeletal C&P exams (back, knee, shoulder, hip). These are the most commonly claimed physical conditions and have very specific exam procedures that veterans need to understand.

Key Requirements:
- 8th grade reading level
- Emphasis on ROM (range of motion) tests
- Clear guidance on pain communication
- 1,500-2,000 words

Please write content for these 8 sections:

### 1. Introduction
- What musculoskeletal exams assess
- Why these exams are so common
- Importance of accurate pain reporting
- What determines your rating

### 2. What the Exam Measures
- Range of motion (ROM) - angles measured in degrees
- Pain on motion vs. pain-free ROM
- Functional loss (what you can't do)
- Flare-ups (how often condition worsens)
- Weakness, instability, locking
- DBQ form breakdown (what examiner documents)

### 3. Physical Tests
- Goniometer measurement (tool that measures joint angles)
- Active ROM (you move it) vs. Passive ROM (examiner moves it)
- Tests for specific joints:
  - **Back:** Forward flexion, extension, lateral flexion
  - **Knee:** Flexion, extension, stability tests
  - **Shoulder:** Abduction, forward flexion, rotation
- Weight-bearing vs. non-weight-bearing tests
- Painful motion testing

### 4. Questions to Expect
- When did pain start?
- How often do you have flare-ups?
- What activities make it worse?
- Do you use assistive devices (cane, brace)?
- Does it affect sleep?
- Can you work? Stand? Sit? Lift?
- Have you had surgery? Physical therapy?

### 5. Preparation Tips
- Find and read the DBQ for your specific joint
- Understand normal ROM ranges for your joint
- Document worst days (flare-ups count!)
- Wear loose, comfortable clothing
- Don't take extra pain medication beforehand
- Bring list of limitations (can't lift >10 lbs, can't stand >15 min)
- Bring imaging reports if not already submitted

### 6. Day-of Guidance
- **CRITICAL:** Stop at the point of pain during ROM tests
- Do NOT push through pain to show full range
- "Painful motion" lowers your rating (in your favor)
- If examiner pushes your joint further, say "That hurts"
- Explain pain level (1-10 scale)
- Communication examples:
  - "I can only bend to here before pain stops me"
  - "This is my pain-free range of motion"
  - "On bad days I can't do this at all"

### 7. Common Mistakes
- **#1 Mistake:** Pushing past pain to show full ROM
  - Why this is bad: Examiner documents "full range of motion" = lower rating
- Taking pain medication before exam (masks symptoms)
- Not mentioning flare-ups ("worse days")
- Not explaining functional limitations
- Wearing restrictive clothing
- Not documenting painful motion during test

### 8. After the Exam
- Document ROM measurements if possible
- Note if examiner pushed past your pain point
- Write down any painful motion
- Challenge exam if measurements seem off
- Request copy of exam report
- Timeline for rating decision

Include a checklist of 12-15 tasks for musculoskeletal exam prep (JSON format):

```json
[
  {"id": "task-1", "task": "Find DBQ for my specific joint condition", "timing": "2 weeks before"},
  {"id": "task-2", "task": "Research normal ROM ranges for my joint", "timing": "2 weeks before"},
  ... (create 12-15 tasks)
]
```

Use current VA musculoskeletal exam procedures and DBQ forms (2025/2026).
```

---

## Prompt 5: Tinnitus/Hearing Loss C&P Exam Guide (Priority 3)

### Copy This Prompt:

```
I need a guide for preparing for Tinnitus and Hearing Loss C&P exams. These are extremely common claims (especially for veterans exposed to loud noise) and have a very specific audiometric test procedure.

Key Requirements:
- 8th grade reading level
- Explain audiometry in plain language
- Address both tinnitus and hearing loss
- 1,200-1,500 words

Please write content for these 8 sections:

### 1. Introduction
- Why tinnitus and hearing loss are so common
- How the exam works (audiometry booth)
- What determines your rating
- Tinnitus rating (max 10%, but service-connectable)

### 2. What the Exam Measures
- **Hearing Loss:** Pure tone audiometry (frequency range)
  - Speech recognition scores
  - Decibel loss at different frequencies
- **Tinnitus:** Recurrent vs. persistent
  - Frequency and severity
  - Impact on concentration, sleep, work
- DBQ form breakdown

### 3. Physical Tests
- Audiometry booth procedure
  - Headphones on
  - Listen for beeps (tones) at different frequencies
  - Raise hand or press button when you hear tone
  - Speech recognition test (repeat words)
- Otoscope exam (examiner looks in ears)
- No pain involved

### 4. Questions to Expect
- When did hearing loss/tinnitus start?
- Was there a specific noise exposure event?
- How often do you hear ringing? (constant vs. intermittent)
- Does it affect sleep?
- Does it affect concentration at work?
- Do you use hearing aids?
- Have you had ear infections or surgeries?

### 5. Preparation Tips
- Review service records for noise exposure documentation
- Document all loud noise exposure (aircraft, gunfire, explosions, machinery)
- Write down tinnitus characteristics:
  - Frequency (constant? or comes and goes?)
  - Sound type (ringing, buzzing, hissing, roaring)
  - Which ear(s)?
  - Impact on sleep, concentration, mood
- Avoid loud noise before exam
- Don't use earplugs during exam

### 6. Day-of Guidance
- **Critical:** Only raise hand when you ACTUALLY hear the tone
  - Don't guess
  - Don't raise hand if you're not sure
  - It's okay to hear nothing at some frequencies
- For tinnitus: Describe honestly
  - "I hear ringing 24/7 in both ears"
  - "It's worse at night when trying to sleep"
  - "I can't concentrate at work because of the buzzing"
- Answer all questions about impact on daily life

### 7. Common Mistakes
- Raising hand when you think you should hear a tone (guessing)
- Not mentioning tinnitus severity (downplaying ringing)
- Not explaining impact on sleep, concentration, mood
- Not documenting loud noise exposure in service
- Assuming examiner knows your military job involved loud noise

### 8. After the Exam
- Request audiogram results
- Document your tinnitus description
- Note if exam felt incomplete
- Challenge if:
  - Booth was noisy
  - Equipment seemed faulty
  - Examiner didn't ask about tinnitus impact
- Timeline for rating decision

Include a checklist of 8-10 tasks for hearing exam prep (JSON format):

```json
[
  {"id": "task-1", "task": "Document all military noise exposure events", "timing": "2 weeks before"},
  ... (create 8-10 tasks)
]
```

Use current VA audiometry procedures and DBQ forms (2025/2026).
```

---

## How to Use These Prompts

### Step 1: Start Research Session
Use Claude with web search enabled (e.g., Claude.ai Pro, or API with web tools)

### Step 2: Copy Each Prompt
Paste prompts 1-5 sequentially into your research session

### Step 3: Review Output
- Check for accuracy against VA.gov sources
- Verify reading level (use Hemingway Editor or similar)
- Ensure tone is empathetic but not patronizing

### Step 4: Format for Database
Once you have the content:

#### For Glossary Terms:
Add via Django admin at `/admin/examprep/glossaryterm/add/` or create data fixture

#### For Exam Guides:
Add via Django admin at `/admin/examprep/examguidance/add/`

Map content to these fields:
- **title** → Guide title (e.g., "PTSD C&P Exam Preparation")
- **slug** → URL-friendly (e.g., "ptsd-exam-prep")
- **category** → Choose from dropdown (ptsd, musculoskeletal, hearing, etc.)
- **introduction** → Section 1 content
- **what_exam_measures** → Section 2 content
- **physical_tests** → Section 3 content
- **questions_to_expect** → Section 4 content
- **preparation_tips** → Section 5 content
- **day_of_guidance** → Section 6 content
- **common_mistakes** → Section 7 content
- **after_exam** → Section 8 content
- **checklist_items** → JSON array from prompt output
- **is_published** → Check this when ready

### Step 5: Test
Visit `/exam-prep/` and click through each guide to verify formatting and accessibility

---

## Additional Content Needed (Optional)

### General Guides (Lower Priority):
- TBI (Traumatic Brain Injury) exam prep
- Sleep Apnea exam prep
- Respiratory conditions exam prep
- Mental health conditions (non-PTSD)

### Supplementary Content:
- "How to Read a DBQ Form" guide
- "Understanding Your Rating Decision" explainer
- "What to Do If Your Exam Was Inadequate" action plan

---

## Content Quality Checklist

Before publishing any guide, verify:

- [ ] Reading level is 8th grade or below (use Flesch-Kincaid test)
- [ ] No unexplained acronyms (or linked to glossary)
- [ ] Specific examples included (not just abstract guidance)
- [ ] Action-oriented (tells veterans what to DO)
- [ ] Common mistakes section is clear and specific
- [ ] Tone is empathetic but realistic (no false promises)
- [ ] All medical procedures explained in plain language
- [ ] Sources cited where helpful (links to VA.gov)
- [ ] Checklist items are actionable with clear timing
- [ ] Content matches database schema fields

---

## Quick Reference: Database Field Mapping

| Content Section | Database Field |
|-----------------|----------------|
| "What is a [condition] exam?" | `introduction` |
| "What the DBQ measures" | `what_exam_measures` |
| "Tests performed" | `physical_tests` |
| "Questions examiner will ask" | `questions_to_expect` |
| "How to prepare" | `preparation_tips` |
| "What to do day-of" | `day_of_guidance` |
| "What NOT to do" | `common_mistakes` |
| "Post-exam actions" | `after_exam` |
| Task checklist | `checklist_items` (JSON) |

---

## Next Steps After Content Creation

1. **Run migrations** (if not done yet):
   ```bash
   docker-compose exec web python manage.py makemigrations examprep
   docker-compose exec web python manage.py migrate
   ```

2. **Access Django admin**:
   - URL: `http://localhost:8000/admin/`
   - Navigate to "Exam Prep" section
   - Add GlossaryTerm and ExamGuidance entries

3. **Test the flow**:
   - Visit `/exam-prep/`
   - Click each guide
   - Search glossary
   - Create a test checklist (requires login)

4. **Accessibility audit**:
   - Tab through pages (keyboard navigation)
   - Test with screen reader (optional but recommended)
   - Verify contrast ratios
   - Test on mobile device

---

## Estimated Time

- **Prompt 1 (Glossary):** 30-45 minutes (one prompt, many terms)
- **Prompt 2 (General Guide):** 45-60 minutes
- **Prompt 3 (PTSD):** 45-60 minutes
- **Prompt 4 (Musculoskeletal):** 45-60 minutes
- **Prompt 5 (Tinnitus):** 30-45 minutes

**Total:** ~4-5 hours of research + content generation

**Data entry:** ~2 hours to add all content to Django admin

**Total time to launch:** ~6-7 hours

---

## Questions?

If content doesn't fit schema or needs adjustment:
1. Check field max lengths in `examprep/models.py`
2. Adjust prompt to generate shorter/longer content
3. Consider splitting very long sections into subsections
4. Use markdown for formatting (bold, lists, headings)

Ready to start? **Copy Prompt 1 into your research session!**
