# Aptitude AI v2 — UI Design
### Matiks-inspired: dark, competitive, rating-driven

> This supersedes the v1 UI doc (which was a calm, Notion-style design). You asked to copy the design direction from Matiks (matiks.com) — a competitive mental-math dueling app with a chess.com-like feel: dark theme, live timers, ratings, streaks, arena framing. This doc adapts that energy to a single-user local app.

---

## 1. Honest Translation Note

Matiks' core loop is **you versus another real person**, live, with a global leaderboard. This app has one user — you — running locally. I'm not going to fake a leaderboard with no one on it or pretend there's matchmaking happening. Instead, the competitive framing is rebuilt around the opponent that actually exists in a single-user context:

- **Duels become "Beat Your Best"** — every practice set is timed and scored against your own rolling personal best for that topic/difficulty, shown live during the question exactly like a duel clock would be.
- **The leaderboard becomes your Reasoning Rating history** — an Elo-style number (see architecture doc §7) that goes up and down like a competitive rating would, just tracked against your own past performance instead of other players.
- **The "Arena" becomes the Practice/Daily Challenge screen** — same visual energy (timer, rating stakes, dark arena backdrop), same stakes-feeling interaction, just solo.

Everything else — dark theme, bold rating display, streak emphasis, fast timed interactions, minimal chrome around the actual question — carries over directly.

---

## 2. Design Thesis

Where v1 was "a quiet notebook," v2 is **"a personal esports arena."** The feeling should be closer to opening a chess.com puzzle rush or a ranked match than opening a study app — immediate stakes, a visible number that moves, a clock running. This is a deliberate trade-off: it's more intense than the calm v1 design, and that's the point — you're copying Matiks because that competitive pressure is a real motivator for daily practice that a quiet UI doesn't provide.

---

## 3. Token System

### Color — Dark, high-contrast, one electric accent

Matiks-style apps in this category (mental-math dueling, chess.com's dark mode, competitive puzzle apps) lean on a near-black base with a single saturated accent used for anything "live" or "at stake." Distinct from the v1 palette entirely:

| Token | Hex | Use |
|---|---|---|
| `--bg` | `#0B0E14` | App background — near-black, cool undertone |
| `--surface` | `#131722` | Cards, question panel |
| `--surface-raised` | `#1B2030` | Modals, the active timer bar |
| `--border` | `#262B3A` | Card borders, dividers |
| `--text` | `#F2F4F8` | Primary text — near-white |
| `--text-muted` | `#8A90A3` | Secondary text, captions |
| `--accent` | `#4CE0B3` | Rating-up, correct answers, primary buttons — electric mint/teal, reads as "positive momentum" |
| `--accent-down` | `#FF5C72` | Rating-down, incorrect answers, mistake counts — used sparingly, only ever attached to a real negative event |
| `--accent-warn` | `#FFC857` | Timer running low, streak-at-risk states |
| `--rating-glow` | `#4CE0B3` at 20% opacity | Background glow behind the rating number when it just changed |

No terracotta, no cream, no soft-neutral palette from v1 — this is intentionally a different app persona.

### Typography

- **Display / Numbers (ratings, timer, streak)** — `JetBrains Mono` or `IBM Plex Mono`, weight 600–700. In a competitive/gaming UI, the numbers that represent stakes (rating, time remaining, streak) should feel mechanical and precise, not friendly — mono at heavier weight does this well and doubles as the "gamer HUD" signal.
- **Headings** — `Inter`, weight 700, slightly condensed letter-spacing (-0.01em) for a sharper, more athletic feel than v1's soft serif.
- **Body / question text** — `Inter`, weight 400–500, sized larger than typical body text (question text especially — this is read under time pressure, legibility at a glance matters more than density).

Type scale:

| Role | Size | Weight | Face |
|---|---|---|---|
| Rating number (Home hero) | 3.5rem | 700 | JetBrains Mono |
| Timer (Practice/Duel) | 2rem | 700 | JetBrains Mono |
| Page heading | 1.75rem | 700 | Inter |
| Question text | 1.5rem | 500 | Inter |
| Body / caption | 0.95rem / 0.85rem | 400 | Inter |

### Spacing & Shape

- Base unit: 8px, scale `4, 8, 16, 24, 32, 48, 64`
- Card radius: `12px` (tighter than v1's 16px — reads more "app/HUD" than "notebook")
- Buttons: `8px` radius, bold fill, no ghost/outline buttons in primary flows — every CTA should read as decisive
- A thin `2px` accent-colored top border on the active question card doubles as a subtle "timer track" that can animate/deplete

### Motion

More present than v1, but still purposeful, never decorative:

- **Timer bar**: depletes continuously, smooth linear animation, shifts from `--accent` to `--accent-warn` in the final 20% of time, no easing (a countdown should feel mechanical, not soft)
- **Rating change**: number counts up/down digit-by-digit over ~500ms when it updates (like a slot-counter), with `--rating-glow` pulsing once behind it
- **Correct/incorrect**: a fast (120ms) full-width flash of `--accent` or `--accent-down` at 15% opacity across the question card — quicker and more assertive than v1's border-only change, matching the "instant feedback" feel of a duel
- **Streak increment**: same quick scale-up as v1, but paired with the flame icon flashing `--accent-warn` briefly
- Page transitions: fast (100ms) cross-fade, no slide — competitive apps cut, they don't glide
- Respect `prefers-reduced-motion`: timer bar still functions (needed for the mechanic) but loses the smooth animation in favor of discrete second-by-second ticks; all decorative flashes/glows disabled

---

## 4. Layout Concept

Still single-column-dominant for reading screens, but denser and more "cockpit-like" than v1 — a persistent status strip is now justified, where v1 explicitly avoided one.

```
┌──────────────────────────────────────┐
│  ⚡ 1247   🔥 12   Day 48               │  ← persistent top status strip:
│                                        │     rating · streak · day count
│  ┌──────────────────────────────┐     │     (mono numerals, always visible)
│  │                                │     │
│  │     [ main content area ]     │     │
│  │                                │     │
│  └──────────────────────────────┘     │
│                                        │
│   Home · Learn · Practice · Review ·  │  ← bottom nav, same structure as v1
│   Roadmap · Progress                   │     but bolder, current tab filled
└──────────────────────────────────────┘     not just underlined
```

Max content width stays at 640–720px — density comes from tighter vertical rhythm and the persistent status strip, not from going full-width.

---

## 5. Page-by-Page Specification

### 5.1 Home

```
┌────────────────────────────────┐
│  ⚡ 1247            🔥 12  Day 48 │  ← status strip
│                                  │
│         1247                    │  ← Reasoning Rating, hero-sized,
│    Reasoning Rating              │     JetBrains Mono, --accent if up
│      ▲ +18 today                │     today, --accent-down if down
│                                  │
│  Today's Mission                │
│  ┌────────────────────────────┐│
│  │ ⚡ Learn              →     ││  ← each row: lightning icon (only
│  │ ⚡ Practice            →     ││     icon exception besides streak
│  │ ⚡ Review Mistakes     →     ││     flame — reads "live/active")
│  │ ⚡ Revision            →     ││
│  └────────────────────────────┘│
│                                  │
│      [ START SESSION ]          │  ← bold, full-width, --accent fill,
│                                  │     uppercase, tracks with letter-spacing
└────────────────────────────────┘
```

- The rating is now the hero of Home, not the greeting — this is the single biggest structural change from v1, matching Matiks putting your rating front and center.
- "START SESSION" replaces v1's quieter "Continue" — same function, more assertive label, matching the arena framing.
- Mission rows keep the same logic as v1 (routes to next incomplete step) but drop the ring-progress motif entirely — v2 doesn't use rings; momentum is communicated through the rating number instead.

### 5.2 Practice ("The Arena")

This is where the Matiks feel needs to land hardest.

```
┌────────────────────────────────┐
│  Ratio · Q4          ⏱ 0:14      │  ← topic/question count left,
│  ▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░   │     live countdown right, timer
│                                  │     bar depletes beneath it
│                                  │
│   [ question text, centered,    │
│     1.5rem, high contrast on    │
│     near-black ]                 │
│                                  │
│   [A] option A                  │
│   [B] option B                  │
│   [C] option C                  │
│   [D] option D                  │
│                                  │
│  Beat your best: 0:11            │  ← small caption under options,
└────────────────────────────────┘     your personal-best time for
                                        this difficulty tier — the
                                        "duel opponent" stand-in
```

- Timer is now **visible by default** — a direct, deliberate reversal of the v1 decision to hide it. This is the core of the Matiks-style redesign: v1 optimized against exam-anxiety, v2 optimizes for competitive momentum. This is a real trade-off worth being aware of — if timed pressure ever starts feeling bad rather than motivating, it's a one-line config flag (`show_timer: false`) to fall back to v1's untimed behavior, not a redesign.
- On answer: instant full-card flash (`--accent` correct / `--accent-down` incorrect), then the Reasoning Rating delta appears immediately next to the timer (e.g. "+14") before the explanation loads below — the rating feedback is immediate, not deferred to a summary screen.
- "Beat your best" replaces v1's silent time-tracking — it's now an explicit, visible target every single question, which is the closest solo equivalent to seeing an opponent's live progress in a duel.

### 5.3 Learn

Kept closer to v1's step-by-step structure — Matiks doesn't really have a "teaching" surface to borrow from, so this stays functional and calm-ish, but restyled into the dark palette with the mono-numeral progress bar at top instead of v1's soft accent line, so it doesn't feel like a jarring theme break mid-app.

### 5.4 Review

```
┌────────────────────────────────┐
│  Review Mistakes                │
│                                  │
│  Probability          12  ⚡981   │  ← topic, count, and this
│  ─────────────────────────      │     topic's own Reasoning Rating
│  Ratio                  4  ⚡1204 │     (lets you see which weak
│  ─────────────────────────      │     areas are also rating-costly)
│  Percentages             2 ⚡1350 │
└────────────────────────────────┘
```

Per-topic Reasoning Rating shown alongside mistake count — this is new in v2 and directly useful: a topic with a low rating *and* many mistakes is a clearer "fix this first" signal than mistake count alone.

### 5.5 Roadmap

Structure is unchanged from v1 (vertical list by category, prerequisite-gated unlocks) but the v1 Mastery Ring motif is dropped in favor of a small per-topic rating badge, consistent with the rest of v2:

```
Intermediate
────────────
✓ Percentages        ⚡1350
● Ratio               ⚡1204   ← current topic, filled dot + rating
  Average              locked
  Profit & Loss        locked
```

### 5.6 Progress

```
         1247
    Reasoning Rating
   [ rating history line chart, --accent line on --bg,
     last 30 days — the one chart in the whole app,
     because a rating's whole point is showing trend ]

Weak Topics (by rating)
────────────
Probability    ⚡ 891
Ratio          ⚡1204

Questions Solved      1,204
Learning Streak        12 days
Best Streak            31 days
```

Unlike v1's explicit "no charts" rule, v2 keeps exactly one chart — the rating trend line — because a rating system's entire value proposition is visible trend over time, and a single number alone can't show that the way it can for a chess/Matiks-style rating.

---

## 6. Component Notes

- **Rating Badge**: new reusable component — a pill showing `⚡ {rating}`, color-coded by recent direction (mint if up this week, muted white if flat, soft red if down). Used on Home, Roadmap rows, Review rows, Progress. This is v2's equivalent of v1's Mastery Ring — the one signature element repeated everywhere.
- **Timer Bar**: reusable component, linear depletion, color-shifts to `--accent-warn` at 20% remaining. Used in Practice and Daily Challenge.
- **Buttons**: single bold primary style only (`--accent` fill, `#0B0E14` text for contrast, uppercase label, `8px` radius). No secondary button style — same "text link for anything non-primary" rule as v1.
- **Icons**: slightly more permitted than v1 (lightning bolt for "active/live," flame for streak, clock for timer) but still no decorative icon set — every icon used maps to a specific live/mechanical concept, never used purely for decoration.

---

## 7. Accessibility Floor

The dark, timed, high-stakes direction makes this section more important, not less:

- Visible focus ring (`2px --accent`, offset `2px`) on all interactive elements, high enough contrast against `--bg` to be clearly visible
- Color is never the only correct/incorrect signal — same as v1, a text label ("Correct" / "Not quite") always accompanies the flash and border change
- Contrast: `--text` on `--bg`/`--surface` meets WCAG AA; `--accent` and `--accent-down` text uses are checked against `--bg` specifically since saturated mint/red on near-black can clip AA at small sizes — use them for large text/icons and fills, not small body text
- **Timer is not a hard requirement to function** — the `show_timer: false` config flag mentioned in §5.2 exists specifically so timed pressure never becomes a blocker rather than a motivator; this should be a real, easy-to-find setting, not a hidden escape hatch
- `prefers-reduced-motion` disables the countdown animation and flash effects, replaced with discrete state changes, per §3

---

## 8. One-Line Summary for the Agent

Near-black background, high-contrast white text, one electric mint accent for positive momentum and a soft red for negative, JetBrains Mono for every number that represents stakes (rating, timer, streak); Reasoning Rating is the hero element on Home and repeats as a badge everywhere else, replacing v1's ring motif; Practice runs on a visible depleting timer against your own personal best, with instant flash feedback and an immediate rating delta on every answer — the whole app should feel like opening a ranked match, not a notebook, while keeping an explicit off-switch for the timer so competitive pressure stays a choice, not a requirement.
