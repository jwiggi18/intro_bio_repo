# Membrane / Cholera Conceptual Arc: Design Notes

**Status:** Scripts drafted. See `membrane-arc-SCRIPTS.md` and `membrane-arc-MAP.md`.
**Week numbers:** match `Weekly_topic_schedule_DRAFT.xlsx` (topic_schedule tab) as of July 31, 2026.
**Covers:** Weeks 2–4 taught as one integrated arc (chemistry of life + cells + membranes are NOT split).
**Anchor case:** Cholera.

---

## ⚠️ DON'T FORGET: line to place in the DIFFUSION video

This video comes **before** the membrane arc. When transitioning from diffusion into
concentration gradients, use this framing:

> **"Diffusion moves things toward balance. Life moves things away from it."**

Why it matters: it pre-empts the "the body tries to reach balance" misconception before
it can form. Cells spend enormous energy *maintaining* imbalance. Equilibrium is death.
Everything later in the arc (gradients as batteries, CFTR as a release valve, chemiosmosis
in Week 13, and action potentials in Week 5) depends on students having this straight from the first time they meet diffusion.

Place it at the **diffusion → concentration gradient transition**, not earlier.

---

## Why cholera as the anchor

Chosen over CF-alone and virus/glycoprotein-alone because it is simultaneously:

- a **transport** story (chloride channel stuck open)
- a **signaling** story (G protein switch welded on)
- a **membrane structure** story (toxin docks on a surface glycolipid)

It covers membranes AND cell signaling, which sit in the same week. CF touches signaling
not at all. CF is retained as the Weeks 7-9 (Genetics) callback: same protein, opposite
failure, opposite direction of water.

---

## Video sequence

| # | Working title | Core content |
|---|---|---|
| 1 | The membrane | Cholera hook. Water, polar covalent bonds, polarity, hydrogen bonding, ionic bonds + NaCl dissociation, phospholipids, self-assembly, closure into a compartment. Ends on: there is now an inside and an outside. |
| 2 | The barrier and the doors | Why charged things can't cross the oily core. Hydration shells. Channels as picky doors. Selectivity. |
| 3 | Why anything moves | Diffusion, concentration gradients, osmosis as diffusion-applied-to-water, aquaporins. |
| 4 | Who's paying | Channels vs. pumps. Gradients are built, not found. Equilibrium is death. **Conceptual hinge, do not merge.** |
| 5 | Cholera resolved | Toxin jams CFTR. Cl⁻ out, Na⁺ follows, water follows through aquaporins. Then ORS and the reversed gradient. |

A **pre-video on solute/solvent and concentration** is needed before video 3.

---

## Decisions made

**Keep Cl⁻, don't cut it.** NaCl dissociates into both ions in video 1, so both are already
introduced with hydration shells. Cholera then uses both: Cl⁻ floods out, Na⁺ follows the
charge. The salt from the demo is literally the salt leaving the patient.

**Lipids are not macromolecules, strictly.** They are not polymers. OpenStax is internally
inconsistent (Ch. 3 is titled "Biological Macromolecules" and includes lipids, but 3.3 never
calls them that and defines them by property, not structure). Teach the distinction out loud
once. The useful point: lipids are the only class of biological molecule defined by *how water
treats them*, which is exactly why they can build a membrane.

**Drop "split personality"** for phospholipids. Not an accepted clinical term and it's
stigmatizing. Replace with a plain description ("two incompatible pieces bolted together")
then give the real word: **amphipathic**, from Greek *amphi* (both) + *pathos* (feeling).

**Hydrophobic effect, water is the actor, not the lipids.** Avoid "the tails are attracted to
each other" or "the tails hide." Correct framing: water molecules rearrange to maximize their
own hydrogen bonds, and clustering the tails is how they do it. Nobody herds the lipids.

**The sheet closes because an edge is unstable.** A flat bilayer exposes tails at the rim, so
it curls until the edges seal. This is the payoff for the opening image (membrane separates
inside from outside): there *is* an inside because water wouldn't tolerate an edge.

**Do not raise size as a competing hypothesis at all.** An earlier draft used "Na⁺ is smaller
than O₂, so it isn't size, it's charge." **Cut that.** It's misleading: bare Na⁺ is ~102 pm and
smaller than O₂ (~173 pm), but *hydrated* Na⁺ is ~358 pm and much larger. The ion is never bare,
so the claim contradicts the hydration-sphere explanation that immediately follows it. Raising a
wrong idea to knock it down also plants it in students who weren't thinking it.

Instead: explain charge and the sphere of hydration on their own terms, and if a student asks
about size, answer then. If a contrast is wanted, compare **water (slight charge, crosses slowly)
to Na⁺ and Cl⁻ (full charge, no crossing)**. Same setup already in the video, only one variable.
Plant the sphere of hydration at the NaCl moment, cash it in at the barrier.

**Notation: once the electron transfers, it's Na⁺ and Cl⁻ forever.** Write bare Na and Cl only
while describing neutral atoms pre-transfer. Name the superscript out loud when it appears ("that
plus is the missing electron"), then never drop it. Solid NaCl is already made of ions, not of
"sodium and chlorine stuck together." Also name the "-ide" convention, since cholera is a
*chloride* story.

**CFTR is a channel, not a pump.** It has no direction of its own. The cell actively loads
chloride above equilibrium using a separate transporter; CFTR is the release valve on a
battery the cell charged itself. The toxin creates nothing. The gradient does all the killing.

**Osmosis is not a special force.** It's diffusion applied to water. Where there's more solute,
there's proportionally less free water. Avoid implying water is "attracted to" or "chases" salt.
Introduce hypertonic/hypotonic *after* the concept, as vocabulary for something already pictured.

**Aquaporins, water does cross bare bilayer, just slowly.** Don't say water "can't" get
through without channels; that's an overstatement students will later find out is wrong. Say
it leaks across badly, and cells that move real volume build dedicated single-file channels.
(Peter Agre, Nobel 2003.)

**In cholera the toxin never touches water.** Aquaporins work perfectly, at full speed, on a
false signal. ORS then reverses the gradient via a sodium-glucose cotransporter the toxin
can't reach, pulling water back through those same aquaporins. Same channels, flipped gradient.

**Gut lumen is topologically outside the body.** Water crossing into the gut has already left
the body before anything is expelled. Reinforces the inside/outside framing one level up.

---

## Mechanism detail deliberately CUT from video

Available for an optional expandable aside on the page, not spoken:

- Retrograde trafficking of the toxin through Golgi and ER
- ADP-ribosylation of the Gsα subunit / blocked GTPase activity
- NKCC1 as the basolateral chloride loader
- Paracellular Na⁺ movement and NHE3 inhibition
- SGLT1 by name

Teachable core is "the toxin welds the off switch." Ten named steps will not increase
understanding.

---

## OpenStax 2e sections this arc pulls

Integration means one video draws from several chapters rather than requiring separate
chemistry lectures:

- **2.1** Atoms, Isotopes, Ions, and Molecules (bonding portion only)
- **2.2** Water
- **3.3** Lipids (phospholipid portion)
- **5.1** Components and Structure
- **5.2** Passive Transport
- **5.3** Active Transport
- **9.1–9.3** Cell Communication (signaling side of the cholera mechanism)

---

## ELQ placement note

Highest-value checkpoint in the arc: **end of video 2**, phrased as *"A cell needs a channel
to move sodium, but oxygen crosses the membrane with no help at all. What's different about
sodium?"* Correct answers land on charge and the sphere of hydration. Wrong answers say
"sodium is bigger," which catches the misconception **without the video having planted it.**

Full checkpoint set is in `membrane-arc-MAP.md`.

---

## Open items

- [ ] Verify final full-year 2025 WHO cholera figures before recording (draft used 565,404
      cases / 7,074 deaths reported through late Oct 2025 across 32 countries)
- [ ] Decide how to handle the "why is cholera still happening" question (answer is war and
      water infrastructure, not biology), worth ~30 seconds, but plan it
- [ ] Write the solute/solvent pre-video
- [ ] Draft video 4 ("Who's paying"), the hinge, and the least sketched
- [ ] Draft the CF counterpart for the Weeks 7-9 genetics block

---

## Reference

- WHO cholera fact sheet: https://www.who.int/news-room/fact-sheets/detail/cholera
- WHO multi-country cholera situation reports: https://www.who.int/publications/m/item/multi-country-outbreak-of-cholera--external-situation-report--32--26-november-2025
- Lumen/SUNY Biology for Majors I (structural model for integrated sequencing):
  https://courses.lumenlearning.com/suny-wmopen-biology1/
