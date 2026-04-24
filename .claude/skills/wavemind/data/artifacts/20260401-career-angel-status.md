# Career Angel Status Check - 2026-04-01

**Participants:** Lily + Jackie
**Topic:** First run of /career-angel status. Comparing master resume against website and generated variants.

## Actionables

- [ ] Add 2026 GTC Women in AI/ML Infra panel to website News grid (need thumbnail image at `assets/img/invited_talks/2026_gtc_modal.png`)
- [ ] Add 2024 Generative AI Summit keynote to website News grid (need thumbnail)
- [ ] Add University of Delaware CAR lab Board Advisor to website Service section
- [ ] Add ICCV '25 to Program Committee list on website
- [ ] Consider adding Projects section to website (Frontend Slides has 12K+ stars)
- [ ] Update bio to mention AliCloud Research Advisor role
- [ ] Update bio to mention Stanford education
- [ ] Run `/career-angel sync-website` to generate actual HTML changes

---

## Round 1: First Status Check
**Lily:** /career-angel status

**Jackie:** Read all three sources in parallel: master resume, website index.md, papers.yml. Also checked for generated resume variants in `~/Documents/lilyzhng/2026/resumes/`.

Findings:

**In Resume, NOT on Website:**

News/Talks missing:
1. 2026 Women in AI/ML Infra @ GTC panel (Modal, Eataly, alongside Hex CTO). High-profile, recent.
2. 2024 Generative AI Summit keynote (Austin). Older but still a gap.

Service missing:
3. UDel CAR lab Board Advisor (only Texas A&M listed)
4. ICCV '25 in Program Committee

Projects (none on website):
5. SofaGenius, SuperGeneral, SkillClaw, Frontend Slides (12K stars), Hand-Draw, WaveMind, PromiseLand

Bio gaps:
6. AliCloud Research Advisor role
7. Stanford education

**On Website, NOT in Resume:** Nothing stale found. Website is a clean subset.

**Generated Variants:** No `resumes/` directory exists. No tailored variants have been created yet.

**Prioritized recommendations:**
- High: GTC 2026 panel (recent, high-profile signal)
- High: ICCV '25 in PC list (simple fix)
- Medium: Frontend Slides project (12K stars is strong)
- Medium: Bio updates (AliCloud, Stanford)
- Low: 2024 Generative AI Summit (needs thumbnail)

## Round 2: The Status Check Was Wrong
**Lily:** The status check doesn't do a good job. It says everything is on the website but not on the resume. That's wrong.

**Jackie:** You're right. I was lazy on the reverse direction. Actual gaps I missed:

Website has things NOT properly reflected in the resume:
- Website PC list includes **IROS '23**, resume PC list does NOT have IROS
- Website says NeurIPS '21, '24, '25 (specific years), resume says '21-'25 (range). Which is correct? They don't match.
- Website says CVPR '22-'25, resume says '21-'25. Resume adds '21 which website doesn't have.
- Website has "Workshop Moderator at Auto.AI" in Service. Resume has "2024 Generative AI Summit" in Keynotes. Same event? Different framing.

The sources have drifted from each other and the status check should have caught this.

## Round 3: One Master File, Everything Else is Generated

**Lily:** There should be a master file. Right now it's partially in PROJECTS.md, partially in resume.md. The resume and website should be artifacts of the master file.

**Jackie:** Read both files. The split is clear:

**PROJECTS.md** (`~/Documents/lilyzhng/Build/PROJECTS.md`) has:
- 10 projects with full thesis, key findings, architecture decisions, links to design docs
- Projects NOT in the resume: Acta, MicDrop, Autoresearch, RL Post-Training, Agents Org (separate entry)
- No experience, publications, patents, education, skills, PC years

**resume.md** (`~/Documents/lilyzhng/2026/Lily_Zhang_2026_resume.md`) has:
- All sections (summary, skills, experience, projects, publications, leadership, keynotes, education)
- Projects are compressed to 1-2 sentence resume bullets
- PC years listed as ranges (potentially inaccurate)
- Patents listed as "various patents" (website has 7 specific entries)

**Website** (`lilyzhng.github.io`) has:
- Its own subset with HTML formatting
- papers.yml has all 7 patents enumerated (more detail than resume)
- PC years differ from resume
- Some events categorized differently (moderator vs keynote)

### Design Question: What Should the Master File Look Like?

It needs to be the single source of truth for ALL professional data:

| Section | Currently lives in | Notes |
|---------|-------------------|-------|
| Bio / Summary | resume.md | Website bio has drifted |
| Experience | resume.md only | Not in PROJECTS.md |
| Projects | PROJECTS.md (rich), resume.md (compressed) | PROJECTS.md is authoritative |
| Publications | resume.md + papers.yml | papers.yml has more detail |
| Patents | papers.yml only | resume.md says "various" |
| Leadership / Service | resume.md + website | Have drifted from each other |
| Keynotes / Talks | resume.md + website News | Different framing in places |
| Program Committee | resume.md + website | Years don't match |
| Skills | resume.md only | |
| Education | resume.md only | |

**Open design questions:**
1. How detailed should projects be in the master? PROJECTS.md level (thesis, findings, design docs) or something in between?
2. Should the master include links to design doc directories, or just the public-facing links?
3. Where does the master file live? `~/Documents/lilyzhng/2026/` or `~/Documents/lilyzhng/Build/`?
4. Should PC years be enumerated individually (not ranges) to prevent drift?
5. How do we handle the patents? Enumerate all 7, or keep the grouped reference?
