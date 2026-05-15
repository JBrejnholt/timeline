<!--
  Rendered version: https://bitecloud.dk/presentations/velux-ai
  This file is the editable Marp source. The website hosts the canonical
  rendered deck; iterate here, regenerate when content changes.
-->

---
marp: true
theme: default
paginate: true
size: 16:9
footer: 'Bitecloud · VELUX Skjern · 2026-05-21'
style: |
  /* Bitecloud-style — direct, calm, opinionated, lots of whitespace */
  section {
    background: #fafafa;
    color: #1a1a1a;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "SF Pro Text",
                 Helvetica, Arial, sans-serif;
    font-weight: 400;
    padding: 80px 110px;
    font-size: 32px;
    line-height: 1.45;
  }
  h1 {
    font-size: 76px;
    font-weight: 600;
    letter-spacing: -0.02em;
    color: #1a1a1a;
    line-height: 1.1;
    margin: 0 0 32px;
  }
  h2 {
    font-size: 48px;
    font-weight: 600;
    color: #1a1a1a;
    margin: 0 0 32px;
  }
  h3 {
    font-size: 32px;
    font-weight: 600;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 0 0 24px;
  }
  strong { color: #c41e3a; font-weight: 600; }
  em { color: #1a1a1a; font-style: italic; }
  blockquote {
    border-left: 5px solid #c41e3a;
    padding-left: 32px;
    color: #1a1a1a;
    font-size: 46px;
    font-weight: 500;
    font-style: normal;
    line-height: 1.35;
    margin: 0;
    quotes: none;
  }
  blockquote::before, blockquote::after { content: none; }
  p { margin: 0 0 16px; }
  .muted { color: #6b7280; }
  .small { font-size: 22px; color: #6b7280; }
  .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 24px; }
  .ribbon {
    display: inline-block;
    background: #fbe9ec;
    color: #c41e3a;
    padding: 6px 16px;
    border-radius: 6px;
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 22px;
  }
  /* Lead slides — title / section breaks / one-liners */
  section.lead {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: flex-start;
  }
  section.center {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
  }
  section.center h1, section.center h2 { text-align: center; }
  /* Big-line slides — for the punchlines */
  section.bigline blockquote {
    font-size: 60px;
    line-height: 1.25;
    padding-left: 40px;
    border-left-width: 6px;
  }
  /* Hide footer + page number on the title slide */
  section.title footer, section.title::after { display: none; }
  ul { margin: 0; padding-left: 0; list-style: none; }
  ul li { padding: 8px 0; }
  ul li::before {
    content: "·";
    color: #c41e3a;
    font-weight: 700;
    margin-right: 16px;
  }
---

<!-- _class: title center -->

# Building on what you already have

### AI on top of the platform we agreed on five years ago

<br>

<span class="muted">Jinhong · Bitecloud · VELUX Innovation Center, Skjern · 2026-05-21</span>

<!--
SPEAKER:
- Land warmly. You know this room. Kasper invited you. Five years ago you
  built the CCoE here; many of these people were on the receiving end.
- Don't introduce yourself formally — Kasper does that. Just smile, "good
  to be back."
- Slido is open from minute zero. Mention it before slide 2.
-->

---

<!-- _class: lead -->

## A story.

<span class="muted">Before I start.</span>

<!--
SPEAKER:
- One-beat slide. Just lets the room settle.
- "Before I get into anything technical, a short story."
- 5 seconds. Move on.
-->

---

<!-- _class: center -->

# Two deer.

<br>

## A lion.

<!--
SPEAKER:
- Tell the deer story aloud. Slide is just an anchor.
- "Two deer are in a field. A lion appears. One deer starts drinking a
  can of Red Bull. The other deer looks at her and says, 'That won't help
  you outrun the lion.' The first deer takes another sip, and says..."
- Pause. Look at the room. Click.
-->

---

<!-- _class: bigline center -->

> I don't need to outrun the lion.
>
> I just need to outrun you.

<!--
SPEAKER:
- Wait for the laugh. Don't talk over it.
- Then a beat of silence.
- "So. That's the joke. Here's why I'm telling it to you today."
-->

---

<!-- _class: lead -->

# AI is not coming for your job.

<!--
SPEAKER:
- Slow. Clear. Don't apologise.
- Pause.
- "That's not the threat. This is the threat."
-->

---

<!-- _class: lead -->

# The engineer in the next building who learned to use AI

# **is** coming for your job.

<!--
SPEAKER:
- This is the reframe. Land it directly.
- "It's not the technology that displaces you. It's a colleague with
  six months more practice than you."
-->

---

<!-- _class: lead -->

## The difference is not intelligence.
## Not experience.

<br>

## It's whether the last six months were
## spent **trying things** — or **arguing about AI**.

<!--
SPEAKER:
- Say each line. Don't rush.
- This is the moment that distinguishes the talk from a generic AI keynote.
- You're not telling them AI will solve everything. You're telling them the
  cost of NOT trying is paid by them, individually.
-->

---

<!-- _class: lead -->

# But.

<!--
SPEAKER:
- One-word slide on purpose. The turn.
- Beat.
- "You have something that engineer in the next building probably doesn't."
-->

---

<!-- _class: lead -->

# You have what they don't.

<br>

- **Factories.** Real ones, that build real windows.
- **Machines.** PackML, MES, axis_2, drive faults.
- **Operators.** Who write notes in Danish at 09:45.
- **Kafka.** The backbone we agreed on five years ago.

<!--
SPEAKER:
- Don't read the bullets. Riff. Look at the room.
- The Danish operator note line will land — they'll smile.
- The Kafka mention is the first foreshadow of the credibility callback.
-->

---

<!-- _class: bigline center -->

> AI without that
>
> is a tourist with Google Maps.

<!--
SPEAKER:
- This is a memorable line. Let it sit.
- "It can find the restaurant. It can't tell you which dish is actually good."
-->

---

<!-- _class: bigline center -->

> With it,
>
> you become **irreplaceable**.

<!--
SPEAKER:
- Hold this slide for 5 seconds.
- "That's what this hour is about. Not the technology. The combination."
-->

---

<!-- _class: lead -->

## Three short stories.

<span class="muted">From the last six months.</span>

<!--
SPEAKER:
- Pick three you can tell in 90 seconds each:
  · one productivity / dev-loop story
  · one Nordic-enterprise pilot story (Saxo/Novo/LEGO appropriate)
  · one "small model doing something specific" story
- Each story is on its own slide so the audience has a visual anchor.
- TODO: Jinhong to fill in the three stories on the next slides.
-->

---

<!-- _class: lead -->

# Story 1

### *[Productivity / dev-loop — Jinhong to write]*

<span class="small muted">Suggested: 60–90 seconds. End with a specific outcome.</span>

<!--
SPEAKER:
- Replace with your strongest "engineer learned to use AI" story.
- Example shape: "Engineer X at Y started using Z six months ago. Now they
  do A in 20 minutes instead of two hours. What's interesting isn't the
  speed — it's what they do with the saved time."
-->

---

<!-- _class: lead -->

# Story 2

### *[Nordic enterprise pilot — Jinhong to write]*

<span class="small muted">From the AI exchange / public sources only. No confidential Saxo detail.</span>

<!--
SPEAKER:
- A real, named or implied Nordic company doing something measurable
  with AI. Frame as pattern, not advertisement.
- Stay within public sources for Saxo; lean on AI exchange notes.
-->

---

<!-- _class: lead -->

# Story 3

### *[Small model, narrow use case — Jinhong to write]*

<span class="small muted">Sets up the demo. Something that COULD be the demo.</span>

<!--
SPEAKER:
- The story that transitions naturally into the live demo.
- Example shape: "Small open-weight model, narrow task, runs on a laptop,
  catches what would have taken three meetings to spot."
- End with: "And it turns out you don't need a research lab to do this."
-->

---

<!-- _class: lead -->

## Five years ago.

<!--
SPEAKER:
- This is the credibility callback. Slow down.
- Look at the people you recognise.
- "Some of you were in the room when we made this decision."
-->

---

<!-- _class: bigline -->

> Five years ago we agreed
> **Kafka** was the right backbone for this platform.
>
> Today the data is flowing through it.
>
> The next conversation is not *whether* to add AI on top —
>
> it is **how to do it on your terms.**

<!--
SPEAKER:
- This is the most important slide in the keynote half.
- Land each clause distinctly. Don't run the lines together.
- The "on your terms" is the entire framing of the rest of the talk.
- After this line, you flip to the live demo. Don't speak over the
  transition; just say "let me show you."
-->

---

<!-- _class: center -->

# Let me show you.

<span class="muted">[ flip to localhost:8000 / Demo tab ]</span>

<!--
SPEAKER:
- Switch to browser, Demo tab, full-screen.
- See TALK_NOTES.md "Live demo" section for per-chip phrasings.
- 10 minutes for the demo. Don't drift past 0:30.
-->

---

<!-- _class: center -->

## [ live demo runs here — minutes 20 to 30 ]

<span class="muted">browser at localhost:8000 — Demo tab → Deployment tab</span>

<!--
This slide is a placeholder so the deck stays consistent if you
accidentally advance during the demo. The browser is the visual,
not these slides. Click back to slides at minute 30.
-->

---

<!-- _class: lead -->

# Where the rest of the Nordic enterprise sits

<span class="muted">After ~18 months of trying things in public.</span>

<!--
SPEAKER:
- Section header for the substance segment.
- "Quick map before I get into specifics."
-->

---

<!-- _class: lead -->

## Most are between

<br>

## **productivity tools** &nbsp;&nbsp;←→&nbsp;&nbsp; **measured pilots**.

<br>

<span class="muted">Very few in production at scale. Almost none with governance figured out.</span>

<!--
SPEAKER:
- Honest mapping. Don't oversell.
- "Productivity tools" = Copilot, Cursor, ChatGPT use across teams.
- "Measured pilots" = a thing in a corner, instrumented, with kill criteria.
- The gap between these two is where this talk lives.
-->

---

<!-- _class: lead -->

# The five practical patterns

<br>

1. **Productivity** — IDE assist, meeting summarisation, search
2. **Software delivery** — code, tests, review, docs
3. **Enterprise data** — NL → query → answer *(what you just saw)*
4. **Agents** — narrow, observable, kill-able
5. **Platform capability** — inference plane, governance, identity

<!--
SPEAKER:
- Walk through these without reading. 30 seconds each.
- Tie #3 back to the demo. "You saw the third one already."
- #5 is the bridge to the deployment view and the consulting pitch.
-->

---

<!-- _class: lead -->

## The trade-off is not

## *open vs commercial.*

<br>

## It is —

<!--
SPEAKER:
- Two-slide structure. This one sets up the reframe.
- "Everyone asks me about open source. Wrong question."
-->

---

<!-- _class: bigline -->

> What needs **control**,
> **locality**,
> **cost discipline**,
> **optionality**?

<br>

<span class="small muted">→ bitecloud.dk/insights/meta-did-not-kill-open-source</span>

<!--
SPEAKER:
- These four words are the framing.
- "Control" — who can see the data.
- "Locality" — where it runs.
- "Cost discipline" — measurable per unit at scale.
- "Optionality" — switch models without rewriting.
- Hint at the Bitecloud article without making it an ad.
-->

---

<!-- _class: lead -->

# Build a thin AI layer.

<br>

## Not a new AI platform.

<br>

<span class="muted">Extend the container + Kafka substrate you already run. The shape we
just deployed — Service, Deployment, ConfigMap — is the shape your
platform team already knows. The AI plane is a new <em>application</em>,
not a new <em>platform.</em></span>

<!--
SPEAKER:
- This is the consulting pitch in disguise.
- Tie back to the Deployment tab from the demo.
- "If you remember nothing else from this hour, remember this."
-->

---

<!-- _class: bigline center -->

> Adoption is not access.
>
> **Governance** must create paths.
>
> **Ownership** makes it real.

<!--
SPEAKER:
- Three-line frame.
- "Access" = anyone can pip install. "Adoption" = it changes how work is done.
- Governance isn't a brake; it's a path with guardrails.
- Ownership = someone whose performance is measured by whether it works.
-->

---

<!-- _class: lead -->

## Three hard questions you should ask me

<br>

- How would I land this without leadership buy-in?
- What's the smallest pilot worth starting?
- Where is AI not the right tool?

<span class="small muted">Drop your own on Slido — the best three go first.</span>

<!--
SPEAKER:
- This is your bridge to Q&A.
- Naming likely hard questions yourself disarms them.
- See TALK_NOTES.md "Anticipated Q&A" for the answers.
- Then: "Slido. Take a minute. I'll pull the three best ones."
-->

---

<!-- _class: bigline center -->

> You don't have to outrun the lion.
>
> You just have to be the engineer
>
> who **tied her shoes**.

<!--
SPEAKER:
- Closing line. Mirrors the opening.
- Smile. Wait. Then: "Thank you. What did I miss?"
- Click to Slido. Pull the first question.
-->

---

<!-- _class: center -->

## Thank you.

<br>

<span class="muted">jinhong@bitecloud.dk · bitecloud.dk</span>

<br>

<span class="ribbon">github.com/JBrejnholt/timeline → talks/VELUX_05_2026</span>

<!--
SPEAKER:
- Leave this up during Q&A.
- The repo link IS the consulting pitch. Anyone who wants to try this
  has everything they need to start tonight.
-->
