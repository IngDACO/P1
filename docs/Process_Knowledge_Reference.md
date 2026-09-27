# Process Knowledge Reference — Schindler F3 Lift Install & Rip-Out

Plain-language recap of everything explained across our conversations, kept separate from the structured Stage/Activity doc. Purpose: give enough real-world context that freeform installer logs (which use slang, abbreviations, and non-linear ordering) can be interpreted accurately.

---

## GLOSSARY

| Term | Meaning |
|---|---|
| Tirak | Temporary installation motor, used to drive the cabin before the permanent motor is belted in |
| Stopblock / blockstop | **Temporary device** (corrected — earlier draft had this as permanent) used during the install. Attached early, alongside the tirak, on the platform; stays in place through the shaft climb and is removed later, alongside tirak removal (Stage 13, Belting & Finishes), not as soon as rails reach the top. Same device across its whole install/removal lifecycle, not two separate components. |
| Inex kit | Schindler-supplied kit of temporary install-assist tools/gear that travels in its own toolbox. Nothing in it stays permanently in the lift. |
| Orange box | The Inex kit's temporary 3-phase power box, used to power the tirak before mains/permanent power is connected |
| COP | Control Operation Panel — the car-call/display unit inside the cabin |
| OKR | Main junction box on top of the cabin where wiring from underneath and inside the cabin converges. Also called **"revision box"** or **"inspection box"** by some installers — same device (Danilo, Sep 2026). |
| PDO | Panel Door Operator |
| Salsis | Tape/reader safety system — appears as "salsis tape" (on single bedplate), "salsis reader" (top of cabin), and "salsis contact" (pit) |
| LIP / LOP | Landing Indicator Panel / Landing Operating Panel — cabling for landing floor displays. Call button wiring is a separate line item (Stage 11). |
| SG | Speed Governor |
| Rots | Install-assist bars used when setting up landing door installation |
| Groutguarding | Metal sheeting covering penetrations and the concrete opening around a door frame, sealing the shaft. Fire-rated — also called **"fire brackets,"** **"fire trims,"** **"fire rating"** (as in "fire rating installed"), and **"fire seal."** All one family of fire-finish work around the landing doors — confirmed (Danilo, Sep 2026), not separate tasks. Uses a black, thick **grout tape** on the guards themselves as part of the material. |
| Bottles | Brackets on the bedplates that hold the belts |
| U/Wing brackets | Two bracket-mounting methodologies used specifically for cabin platform/yoke assembly |
| Yoke | The base structure the car assembly is built on |
| Fillerweights | Counterweights thrown into the **CW tank** — not the car's own platform, despite "platform structure" wording that's caused confusion before (Danilo, Sep 2026, clarified). Can be thrown at any point from when the car platform first goes on (easiest then, since only the platform is up and the tank is clear to access) through right up until belting — by belting time, roughly 50% of the tank needs to be filled to balance the cabin's weight. |
| Fishplates | Connector plates that come with the rails; arrive greasy and need cleaning before being fitted to the rail's male side |
| Kemset | A chemical resin anchor/fixing system — has a drying/curing time (seen as long as 18h) that can bottleneck progress if not planned around |
| DBG | Distance Between Guiderails |
| Governor tension sheave | Also called tension pulley, tail sheave, jockey pulley, or **Jenny wheel** (and its spelling variant **Genie wheel**) — the pit-mounted tensioning device for the speed governor rope |
| Trimmer beam | Structural beam spanning the top of the shaft, min. 2-tonne WLL, installed with 16mm throughbolts. Holds the lift's weight during install/rip-out; subject to a **snap test** to verify load capacity before use. This is the "top-of-shaft beam/hook point" referenced in the rip-out process. |
| Hogan unit | Emergency battery unit, mounted on top of the car roof next to the OKR |
| Reverses | The front walls of the cabin — the ones that form/frame the door opening |
| Minifor | **Corrected (Danilo, Sep 2026)** — a secondary rigging/lifting aid, mounted (e.g., to the ceiling) and used alongside the tirak, similar in role to the electric chain block. This is the device the R2 "electric chain block" description was already analogizing to. (Earlier draft had this as an alternate name for the winch/motor — wrong, replaced.) |
| Genie wheel | Alternate spelling/mishearing of "Jenny wheel" — same governor tension device (pit-mounted rope tensioner). Confirmed (Danilo, Sep 2026). |
| TKE | ThyssenKrupp Elevator — a different lift company/brand. Confirmed as a genuine reference, not a typo or mislog (Danilo, Sep 2026). |
| False car | A temporary construction car/platform, distinct from our lift's actual cabin — raised by a sky climber instead of a tirak. Confirmed (Danilo, Sep 2026): gives rise to two of its own Stage 1 (Set Up) activities — see Sky climber and Sky lock. |
| Sky climber | The false car's motor equivalent (Danilo, Sep 2026) — works the same way a motor does. Needs a rope installed, needs its own dedicated power, and has a pendant (control). Own Stage 1 activity, conditional (only on jobs using a false car). |
| Sky lock | The false car's speed governor equivalent (Danilo, Sep 2026) — simpler than the sky climber: just needs the rope installed, and attaches directly to the safety gear. Triggers the same way any speed governor does. Own Stage 1 activity, conditional (only on jobs using a false car). |
| Hilti plates | Anchor/mounting plates (Hilti = fastener brand) used for motor installation at the top of shaft. Confirmed (Danilo, Sep 2026). |
| Mains | Generic term for the electrical power supply (building/permanent power). Confirmed (Danilo, Sep 2026) — context determines whether a log using this term means initial power connection/wiring or the Stage 13 permanent mains changeover. |
| CCEW | Certificate of Compliance for Electrical Work — a compliance document, part of Stage 14 (Certification & Handover) paperwork. Confirmed (Danilo, Sep 2026). |
| The well | Informal term for the shaft. Confirmed (Danilo, Sep 2026). |
| CAN line | A CAN-bus communication line run to the options box. Confirmed (Danilo, Sep 2026). |
| Belden | A cable brand name — not a task or component, just a brand reference seen in logs (e.g. "joined flex with Belden"). |
| Compensation chain | Purely mechanical component, installed late in the job (well after most other work is done) — see Stage 13 (Belting & Finishes). Confirmed (Danilo, Sep 2026). Has its own sub-parts: the chain itself, chain **guides**, and a chain **safety rope**. |
| Loadcell | Alternate name for the existing weight sensor (under-cabin wiring, Stage 10) — same device, not a new component. Confirmed (Danilo, Sep 2026). |
| Lightrays | Door safety light-curtain sensors, top of cabin (Stage 10). Also called **"photocell"** and **"curtain of light"** — same device, alternate names. Confirmed (Danilo, Sep 2026). |
| Magnet tape reader | Not a separate component — refers to the combined salsis/magnet-reader system (salsis tape, Stage 6, and magnet reader, Stage 10). Confirmed (Danilo, Sep 2026). |
| Magnet strip's top bracket | Mounting bracket hardware that's part of the magnet reader (Stage 10, Top of cabin) — not a separate task. Confirmed (Danilo, Sep 2026). |
| Cube / Pixel | **Not interchangeable — distinct components.** Cube = the modem, connects the lift to the internet (needs 2 antennas fitted for cellular reception). Pixel = an intercom unit that also connects to the internet, separate function from the cube. Most lifts have one or the other, but some jobs have both — don't assume a job needs only one just because it's more common. **Pixel can be mounted in multiple locations (Danilo, Sep 2026):** on top of the cabin next to the OKR box, inside the cabin at the COP, underneath the cabin (rare), inside the controller unit, in the headroom, and in the pit. Don't assume "cabin/headroom only" — read each log for which location it names. |
| Packers | Shimming material used for alignment on rings, rails, and headers. Recurring bottleneck when unavailable — same delay pattern as Kemset drying time. |
| Wadges | Wedges — used to secure belts |
| Anti-twists | Belt anti-twist device |
| Egress (device/step) | Safety egress point — appears both in Pit Mechanical (ladder/step) and Landing Doors (door blade tuning) |
| SWL | Safe Working Load — rating/plate installed on the top-of-shaft beam (R1) |
| TOC | Top Of Cabin/Car |
| KTS | Safety contacts |
| SIS | A switch box, part of the controller |
| Toe guards | = skirts/kicks. The plate at the edge, under the sill. |
| Buffer stands | One of two components on a rubber buffer. Sent longer than needed, then cut per job to set the exact travel limit for that lift. |
| Buffer tops | The other component of a rubber buffer, paired with the buffer stand. Note: hydraulic buffers are a separate type from rubber buffers — expect that variant on some jobs too. |
| Governor bedplate | Distinct component from the motor bedplate — not the same plate, don't merge these. |
| Motor bedplate | Distinct component from the governor bedplate. |
| Striker plate | The side of the CW tank that hits the buffer. The cabin also has one, but it always comes pre-assembled (never a separate install step). |
| Bridging (landing doors) | Temporary electrical bridge on landing door circuits — this is an **Installation-track activity** (Landing Doors / Pit-Control Wiring), not part of rip-out, even if it happens to be logged on an early/rip-out-adjacent day. |
| Z side | Nickname for the single-side bracket — called "Z side" because the bracket is shaped like a Z. |
| Z side bedplate | = the speed governor bedplate. Same component, alternate name (referring to which side/bracket it sits against rather than its function). |
| Combo bracket / combination bracket | Another name for the omega bracket. Same component. |
| Top bow | The top section that joins the two uprights together, completing the frame structure at the top of the cabin (Stage 4, alongside uprights). |
| Cradle | Another term for the platform (Stage 4). |
| Finals | The final/top rail lengths — cut to size before being installed at the top of the shaft, since standard rail lengths rarely divide evenly into the full shaft height. |
| Millsons kit | The kit used to install motors. |
| 5500 kit | The Inex kit variant specific to the 5500 lift model. |
| Chisel pit | Concrete cutting/chiseling work in the pit — typically for leveling or sump-related adjustments. |
| Chaser job | Cutting/expanding concrete door openings that were made too small for the new lift — a **design-side error, not an installer error**, and uncommon. Distinct from routine door-opening prep cuts. |
| Cages | Metal-built protective hoarding/barrier, as opposed to timber hoardings — same activity (Rip-Out R0, Hoardings & protection), different material. A log mentioning multiple "cages" (e.g. "three cages") usually means one per landing level, not multiple lifts. Like gates, cages also get stacked/packed at Closeout once no longer needed (Stage 13 Pack Up). |
| Gates | **Distinct from cages, not the same thing** (correcting an earlier best-guess note). Gates get stacked on pallets, folded and compacted, ready for pickup/removal — this happens toward the end of a job. A log entry like "stack gates" is a Closeout-phase logistics task (packing/staging for collection), not a Set Up hoardings task. |
| Builders lift | A lift used temporarily by the builder to replace their construction hoist and continue building works, ahead of final handover to the client. Requires its own interior protection (floor, walls, ceiling) and protection at every landing door (frame protection) so it stays in good condition through construction use. A distinct scope item, separate from both Rip-Out and standard permanent-lift Installation — not every job has one. |
| Electric chain block | Secondary rigging tool set up alongside the tirak during R2 — electric-powered, functions like a chain block, similar in spirit to a minifor. Used in R3 for controlled lifting/lowering of the car and landing the CW tank. |
| Working deck | Temporary platform built in the shaft for rip-out access. Optional and job-specific — not built on every job. |
| Liftronic | A company acquired by Schindler. Liftronic-branded lifts are Schindler lifts — no functional difference. A log referencing Liftronic isn't automatically a different job/company. |
| Laser plumb | Alternate method to physical plumblines — a laser point placed in the pit replaces the plumbline/weight/template setup. Faster, and skips the need for a top-of-shaft template installation. |
| Snap test | Load-capacity test on the trimmer beam/hook point. Should be performed at the very beginning of a job — doing it mid-job is a mistake and a safety risk. Applies to **both** Rip-Out (R1) and fresh Installation jobs (Stage 1), since any job needs a verified hook point before relying on it. Also called a **"pull test"** — same test, different name. |
| Governor tension device ("Jenny wheel") | The pit-mounted speed governor rope tensioner (see also Governor tension sheave). Gets pinned to the rail as part of installation — happens on every job. **"Jenny wheel" is the confirmed correct term** (earlier logged as "yemny wheel" — a mishearing/typo). |
| Speed governor (full system) | Spans three locations, installed at different points in the job: the governor device itself on the single/Z-side bedplate (Stage 6), its rope running down to the tensioner device pinned to the rail in the pit (Stage 8), and the same rope attached to the cabin (Stage 4). A log saying "speed governor on cabin" refers to the rope attachment, not a second device. |
| Gauge / Guage | Installer shorthand for calibrating rail brackets to correct alignment — e.g. "gauge top level" = calibrating the top ring's brackets. Not a distinct component or task, just common phrasing for bracket calibration. |
| Ducting (shaft or headroom) | A protective covering placed over wiring already being run — not a separate task. Common on glass shaft jobs and others where full wiring coverage is specified. Maps to the same underlying wiring tasks (Stage 9 or Stage 11), not a standalone activity. |
| Change over mains | Transitioning the lift from temporary power (tirak/Inex kit) to permanent building mains. A Closeout-phase task (Stage 13), logically following tirak removal. |
| Glass shaft protection | Protective covering for glass shaft panels, applied before rip-out begins — falling debris during demolition can crack/break the glass. Same activity as protecting the floor (Rip-Out R0, Hoardings & protection), not a separate one. |
| MBB | Motor bedplate (confirmed abbreviation). "Installed/levelled MBB" = the same task as "Install motor bedplate" (Stage 6). |
| Uprights | Two structural frame members that are part of Car Assembly (Stage 4) — not a separate "superstructure" stage. Installed alongside rings/rails, before bedplates go in. |
| Cable tray | Physical cable management infrastructure installed as part of Shaft Wiring (Stage 11) — distinct from the wiring itself. |
| Sump hole | An old sump/pit hole needing filling — treated the same as the existing "seal machine room / shaft penetrations" task (Stage 6), not a separate one. |
| Roping | Informal term. There's more than one rope-using device on a job (permanent speed governor, temporary speed governor, tirak, minifors), but "roping" as an informal log entry specifically means the lift was being **belted** that day (Stage 13, Install belts) — not literal rope installation. |
| Load(ed) the tank | Informal for loading fillerweights into the CW tank (same task as "Throw fillerweights," Stage 4/5). |
| Flooded the shaft/pit (with rails) | Informal for placing rails inside the pit/shaft, staged and ready for install. **Counts as progress** — not just material staging. |
| AESD | Alternate way of saying/logging the AED box (Stage 9 Headroom Wiring, optional electrical box). Same component. |
| KSS switches | Safety switches. Confirmed real component — added to Task Breakdown under Stage 6 pending more detail on exact mounting location. |
| Main shed | A confirmed, real (not informal/nickname-based) staging location — distinct from informal ad-hoc staging place names. |
| Door springs | Same thing as "door weights" (weights/strings providing constant closing force, Stage 7) — just a different way of naming the same component. |
| Salsis bracket | Mounting bracket/hardware for the salsis unit, not a separate component — part of "Install salsis tape" (Stage 6). |
| Calcius tape | Typo/mishearing for "salsis tape" (Stage 6). |
| Twist plates / belt twist | Alternate way of referring to the anti-twist device (belt anti-twist). |
| Chase (near call buttons) | Prepping/adequating the concrete for call button installation — not a general term, specific to that context (Stage 11, Call button wiring). |
| Flap disc / manual filer | Two tools used to file down steps and protuberances at rail joints where two rail lengths meet — a flap disc is fitted to a grinder; the manual filer is a hand tool. See "File rail joins," Stage 13. |
| Strip (third meaning) | Beyond Stage 2 prep-strip and Rip-Out-strip, "strip" at Closeout means removing **all** protective plastic film from the finished lift before handover — cabin interior, COP, decoration ceiling, walls, doors, landing doors, landing frames, controller unit, etc. See "Final finishes/touch-ups," Stage 13. |
| CW dumbbell / CW belt keepers | The dumbbell is the point on top of the CW tank where the belts connect and pick up the CW. The belt keepers sit on top of the tank around the dumbbell, keeping the belts contained and clear of the installer for safety. Installed together (Stage 5). |
| Toe guards | Two separate, real, distinct tasks share this name — confirmed (Danilo, Sep 2026): landing toe guards/skirts (under the landing sill, Stage 7 — "Install skirts") and cabin toe guards (under the cabin sill, Stage 4 — "Install cabin toe guard"). Same name, different pieces — check context for which one a log entry means. |
| Balustrades | Alternate term for a handrail — context-dependent, can mean either the cabin interior handrail (Stage 4, "Install cabin interior handrails/kickplates/bumpers") or the rooftop handrail (Stage 4, "Install rooftop handrail"), depending on which the log is describing. Confirmed (Danilo, Sep 2026). |
| Fire switch | A keyed switch, distinct from the groutguarding/fire-brackets/fire-trims/fire-rating/fire-seal family — confirmed (Danilo, Sep 2026) as its own real component. One system, two install locations: at the landing call button box on the main level (Stage 11, Door wiring) and inside the cabin at the COP (Stage 10, Inside cabin). |
| Christmas trees (wiring) | Informal term for wire-routing clips/fixings used to run and secure cable — not a standalone component or task, just generic hardware supporting whichever wiring task is active. Confirmed (Danilo, Sep 2026). |
| Option box (security) | The connection point between the lift and the building: a flex cable runs out to the cabin on the lift side, while all building-supplied services (cameras, swipe/card readers, and any other device the building wants integrated) land on the box from the building side. |

---

## RIP-OUT: CABIN WEIGHT CAN FORCE A REEVING-RATIO CHANGE

If the old cabin is too heavy for the intended tirak ratio (e.g. 2:1), installers strip components to lighten it before attaching ("make lift as light as possible" in logs). If lightening still isn't enough, the ratio itself gets upgraded (e.g. 2:1 → 4:1) rather than proceeding underpowered. Log entries about lightening the cabin belong to the "Transfer to Temporary Drive" phase, even though they can read like general rip-out work and appear interleaved with full rip-out entries — starting this before rip-out fully completes is normal on real jobs, not a sequencing error.

---

## RIP-OUT PROCESS (narrative)

0. **Set up** — same logic as Installation's Set Up stage: toolbox/gear delivery for the installer, delivery of the rip-out kit (tools/gear specific to rip-out), hoardings & protection, and general preparation of the building/site/compound. Happens before possession is taken. Since rip-outs happen in existing (usually occupied) buildings, **deactivating a nearby smoke detector** before work starts is a near-universal part of this stage — as is **protecting glass shaft panels** where present, since falling debris during demolition can crack or break the glass (same logic and same activity as protecting the floor). Protection can be timber **hoardings** or metal **cages** — same activity, different material depending on the job. Some jobs also build one or more temporary **working decks** in the shaft for rip-out access — optional and job-specific, not assumed on every job.
1. **Take possession** of the existing lift, shut it down.
2. **Initial electrical isolation.**
3. If there's no existing hook point/beam at the top of the shaft (common), the old cabin is driven in **inspection mode** (still live) to access the top and install a beam, including its **SWL (Safe Working Load) rating plate**. This beam work is often supplied/completed by Schindler's supply chain (including Liftronic, a company Schindler acquired — same lifts, no functional difference) and can span more than one log entry, including follow-ups for missing bolts.
4. **Mount the tirak**, attach it to the old cabin, hang it on the hook — cabin is still live at this point. An **electric chain block** — electric-powered, functions like a chain block, similar in spirit to a minifor — often gets set up alongside the tirak as a secondary rigging tool, used later for controlled lifting/lowering of the car and CW tank during rip-out.
5. Connecting the tirak to power usually means routing mains through the Inex kit's **orange box**, which requires killing the lift completely. So **before the final kill**, the cabin is positioned at the correct height, since it can't be moved again once dead.
6. **Fully kill the lift electrically.**
7. Drive up using the tirak to collect the cabin on the temporary motor, **releasing pressure from the old ropes/belts** (traction lifts) or **detaching the piston** (hydraulic lifts) — now the cabin moves freely under the tirak alone.
8. Confirming the lift is fully dead is usually **implied** by the orange-box connection rather than a separately logged step — once mains power is routed to the tirak, the lift is killed and never goes live again. If an installer does explicitly log a dead-check, it's treated as part of the tirak installation step above, not its own phase.
9. **Rip out every component** — including rails and rings — unless the client specifically wants certain components left in place (common request; historically logged as sills/door frames, but this generalizes to anything a client wants retained, e.g. superstructure — doesn't affect removal of anything else). For hydraulic lifts, this includes draining/emptying the oil tank in the machine room, removing the hose that runs through the shaft wall to the ram, pumping remaining oil, and removing the ram/piston and hydraulic structure. Hydraulic lifts have rails too, same as traction — rail removal isn't traction-exclusive. Watch for **tool-access blockers** here — a job can stall not just from missing consumables (bolts/packers) but from a needed tool being locked away with a colleague working a different job.
10. Once fully stripped, rip-out is complete (its own 100%, separate from Installation's 100%) and Installation can begin.

Note: stages R2 (tirak install) and the old separate "transfer to temporary drive" step are merged into one stage — in practice they read as one continuous activity in the logs, not two.

**Universal across lift types.** This process applies to any rip-out — traction or hydraulic — read the log and place entries in the right stage; no separate hydraulic/traction process split at the stage level.

---

## INSTALLATION PROCESS (narrative)

### Mechanical

**Set Up** — arrival on site: receive toolbox, receive Inex kit, take delivery of the lift itself (counting all boxes against the manifest, checking codes especially on multi-lift sites so kits don't get mixed up), site induction/paperwork, a snap test (also called a pull test) on the trimmer beam/hook point (should happen right at the start — doing it later in the job is a mistake and a safety risk), hanging temporary work lighting, and building the compound/hoardings (including for temporary builds like at an airport concourse). Some jobs also include installing and protecting a **builders lift** (see glossary) — a separate, conditional scope item, not on every job.

**Prepping** — often apprentices/helpers, sometimes the installer: clean rails and fishplates (both arrive greasy for rust protection), fit fishplates to the rail's male side, prep doors (panels, frames), prep cabin walls, cabin doors, cabin reveals, COP, sills, landing headers, cabin panels, cabin header.

**Plumbing & Survey** — set the plumb template, build the frame it sits in (always at the very top of the shaft), throw the plumblines with weights attached, let them settle under gravity, record the resting measurements on the wall as reference points, install pit plumb brackets and adjust them back to those references, then survey to check the lift's planned position against the real shaft. The template/frame gets removed once no longer needed.

**Car Assembly** — install the first 2 rings (each with 1 omega/combination bracket + 1 single bracket per Schindler's system), first 2 car rails, guide shoes, U/Wing brackets (used specifically for platform/yoke assembly), yoke/base (leveled), platform (also called a "cradle"), cabin sill, then build the cabin itself — walls (including the "reverses," the front walls forming the door opening), doors, ceiling (roof), the two structural uprights plus the top bow that joins them together, header, COP (mechanical mounting), interior handrails/kickplates/bumpers, the spear (door interlock mechanism, mounted on the cabin door header) — attach the tirak and stopblock (both temporary — the stopblock comes off later once rails reach the top, see Shaft Climb & Bedplates), attach the speed governor rope to the cabin (the other end runs to the tensioner device — the "Jenny wheel" — in the pit, see Pit Mechanical), do a quick initial calibration of the safety gripper, install the rooftop handrail, install the cabin toe guard (under the cabin sill — a separate, real component from the landing toe guards/skirts installed later in Landing Doors), earth the cabin platform, and install a mirror if the job spec calls for one. Fillerweights (into the CW tank, not this stage's own platform — see Fillerweights entry above) are typically thrown once the platform is on and before cabin walls go up, since that's the easiest access point, but they're not strictly sequential — they can go in any time up through right before belting.

Note (Danilo, Sep 2026): the cabin roof/top structure ("rooftop pieces") is rigged up bit by bit and dropped into place on top of the cabin walls, then bolted together — not built in one piece. A log describing the roof as being "up ready to drop" or similar mid-process wording reflects this staged rigging method, not a separate task.

**Counterweight (CW) Assembly** — first 2 CW rails, CW guide shoes, props, CW tank.

**Shaft Climb & Bedplates** — repeating the ring/rail install pattern all the way up the shaft (both car and CW sides — both needed before bedplates can go in), then installing the motor bedplate (omega side — holds the motor and the belt-holding "bottles") and the single bedplate (single side — holds the speed governor, salsis tape, and more bottles). Sealing machine room and shaft penetrations also belongs here — it comes up on nearly every project, rip-out or not, since even brand-new installs commonly have leftover or code-required penetrations to close.

**Landing Doors** — install the rots (assist bars), then sills, frames, headers, groutguarding, door panels, skirts, keepers (lock keeper plates), and door weights/strings (constant closing force), then tune the doors. The spear (interlock mechanism) mounts on the cabin door header, so it's installed as part of Car Assembly rather than here. Rollers come pre-fitted with the headers and are never logged as a separate install — they only ever show up as a tuning entry. Keepers and the spear can each be logged either at install time (Landing Doors / Car Assembly respectively) or later as a tuning entry (Commissioning & Tuning) — placement depends on whether the log uses an install/prep verb or a tune verb.

**Pit Mechanical** — ladder, striker buffers, the car and CW buffers (trimmed for precise clearance), the CW screen (physical barrier segregating the CW tank from the rest of the pit for safety), and the governor tension device (also called tension sheave, tension pulley, tail sheave, or jockey pulley — the pit-mounted device that keeps tension on the speed governor rope). Pinning this device to the rail is part of its installation and happens on every job. Some jobs need pit concrete cutting/chiseling for leveling or sump-related adjustments ("chisel pit").

### Electrical

**Headroom Wiring** — install the electrical boxes (AED optional, VAF/drive, option box, cube and/or pixel for connectivity, switch JH), wire them all, then spin the motor as a test. Some jobs enclose this wiring in protective ducting — same underlying task, just with a covering, not a separate one. The drive unit needs clear room from the lift's actual travel path — mounted too close, it can end up in the way and require relocation after the fact (seen as rework on at least one job). Applies whether the controller sits on the lift's top frame or in a separate machine room. **Real-world variant:** many installers wire only the minimum top-frame/controller subset first, specifically so they can belt in the permanent motor and remove the tirak early — driving on the quieter, faster permanent motor sooner rather than waiting for full electrical completion.

**Cabin Wiring** splits into three zones:
- *Under the cabin:* weight sensors (also called "loadcell" — confirmed same device, Danilo Sep 2026), alarms, safety gear contacts, speaker, traveller/flat/flex cables.
- *Inside the cabin:* COP wiring (down to underneath and up to the OKR), ceiling decoration wiring (lights, fans), the COP-side fire switch (keyed — see Fire switch glossary entry for its matching landing-side install).
- *Top of the cabin:* OKR box, salsis reader, magnet reader, wiring from the cabin header/PDO, lightrays (door safety sensors), top-of-car emergency light, speaker, flex cables. The OKR is where wiring terminates from all three zones — underneath, inside, and top — including both the main flex/traveller cable and the optional second flex cable.

**Shaft Wiring** — door wiring (LIP/LOP cables, door locks, call buttons, and the landing-side fire switch at the main-level call button box — see Fire switch glossary entry for its matching COP-side install), and the "line" (contact cable run to pit, power cable for lights, the lights themselves, cable tray for cable management, and magnet flags). On glass shaft jobs and some others, this wiring gets fully enclosed in ducting for protection — same task, just covered, not a separate one. Magnet flags have branching install logic: if landing door headers don't come with magnets built in, small rounded magnets get mounted on the rails, ~8mm from a cabin-mounted magnet reader. If the headers DO come with integrated magnets, the reader instead mounts on the cabin door header, keeping the same 8mm gap to the magnet on the landing header.

**Pit Wiring** — stop button box for the pit ladder, switch light, pendant, GPO (power outlet), SG contact, ladder contact, salsis contact, buffer contacts.

### Closeout

**Belting & Finishes** — install the permanent belts (motor, CW, cabin), change over the lift's power from temporary (tirak/Inex kit) to permanent building mains, remove the tirak gear and all Inex kit components, pack up, clean the shaft, file rail joins, install oilers, final touch-ups. Belting only actually requires the bedplates/motor to be ready plus minimum controller wiring — not full completion of every electrical stage. **Inference rule:** the tirak (and other Inex kit gear) being picked up and returned to the Schindler warehouse is strong indirect evidence belting is complete and the tirak is removed, even with no explicit "installed belts" log entry — same logic as the existing prep-implied rule.

**Commissioning** (added from comparing against a working dashboard, not yet validated against real logs) — Leveling & Adjustments, Testing (load/speed/safety), Certification & Handover.

---

## CHRONOLOGY-DEPENDENT & VAGUE LOG ENTRIES

Some recurring log phrasings are genuinely ambiguous on their own — the fix is reading them against where the job is chronologically, not guessing.

- **"Under the cabin work"** — can mean mechanical or electrical work, both of which happen under the cabin at different points in the job. Read chronological order: if car rails aren't up yet, it's mechanical (Car Assembly). If rails are already up (Shaft Climb & Bedplates has progressed), it's electrical (Cabin Wiring, under-cabin zone).
- **"Pit work"** — same logic. If pit items like the ladder and buffers aren't installed yet, it's mechanical (Pit Mechanical). If they are, it's electrical (Pit Wiring).
- **"Pit doors" (vague, no further detail)** — defaults to mechanical installation (Stage 7, Landing Doors) rather than being left unscoreable.
- **"Flex cable" (no zone specified)** — treat as both the Under-cabin and Top-of-cabin flex cable tasks being done, not just one.
- **"Tune panels"** — part of tuning doors (Stage 7's "Tune doors" activity, not a separate item).
- **"Controller wiring"** is part of Headroom Wiring (Stage 9), even when logged alongside or near shaft wiring entries — confirmed (Danilo, Sep 2026).
- **"Roping"** is a generic verb spanning multiple specific rope tasks (CW rails, governor rope, car rope, rope clamps, etc.) — confirmed (Danilo, Sep 2026) it places wherever the specific rope task is contextually active, same handling as "contacts." Don't default it to one fixed stage.
- **"Car park lock," "park switch," "floor level switch," "limit switches," "top stop switch"** — confirmed (Danilo, Sep 2026) these describe a different (TKE) elevator system sometimes encountered on shared sites, not our own Schindler F3 installs. Not added as tasks — ignore these terms if they show up on a Schindler job with another crew present.
- **Job name spelling variants** — an unfamiliar job-name spelling that closely resembles the current job's actual name is almost certainly a typo, not a genuinely different job.
- **"Strip" on an Installation job** means prepping — stripping/peeling protective film or packaging off a new component (e.g. "strip landing sills") — not removing an installed one. Only read "strip"/"remove" as actual removal on a Rip-Out job or when the component was clearly already installed.

## RECURRING REAL-WORLD PATTERNS WORTH KNOWING

- **"Contacts" is a generic term used all over the lift**, not one specific component — safety gear contact (under cabin), speed governor contact (top and bottom, at the pit tensioner), pit ladder contact, hydraulic buffer contacts, bottles contact, and — when the rooftop handrail is foldable — a contact there too. When a log names the specific location, it maps to that existing item. When it doesn't (just "fixed/installed/tuned contacts"), it defaults to Commissioning & Tuning as a general entry rather than being guessed into a specific system.
- **Induction and daily pre-start don't count as progress**, even though they're near-universal, recurring log entries. Induction usually happens once, on the first day at a new job; pre-start happens every day. Both sit under Logistics & Site Support.
- **Hollow/inadequate brick substrate** has come up more than once across different lifts, requiring either custom fabricated brackets (e.g. slab-to-slab metal gear on the Z-side) or extra fixing work — see also the on-site bracket-cutting workaround noted above, same general category. Common enough on this kind of site to watch for as a recurring theme, not a one-off.
- **Door header/panel mismatches** requiring cutting, redrilling, and metal work can cause multi-day delays.
- **Kemset drying time** (resin anchor curing) is a genuine bottleneck installers plan around — one log explicitly cited an 18-hour cure time limiting how much could be done in a day.
- **Multi-lift jobs** track progress per lift, independently.
- **Helper/driver logs** don't carry independent progress weight — only the installer-of-record's log for a given day counts; helper entries are read for context only.
- **Generic "helped [name] on lift X" entries** — leave unscored ONLY when truly no detail is given. If the entry names even a specific task or component (e.g., "helped level the car," "helped with prep and inductions"), credit that task at appropriate confidence rather than defaulting to unscored (Danilo, Sep 2026). Entries with genuinely nothing beyond "helped [name]" are typically logged by helpers just following instructions without noting specifics, and stay unscored.
- **Chain block is a general-purpose rigging tool, not Rip-Out-specific** — confirmed (Danilo, Sep 2026) it's also used during Installation (e.g., lifting the motor into place at the top of shaft), not only for car/CW-tank handling during R3.
- **On-site bracket cutting is a related, recurring practical workaround**, not a standard prep step — confirmed (Danilo, Sep 2026) as something crews do to solve fit/alignment problems as they arise, same general category as the hollow-brick-substrate/custom-fabricated-bracket pattern below.
- **Site evaluation drill** — a periodic safety/evacuation drill, logged with a duration (e.g., "1 hour"). Non-progress, Logistics & Site Support (Danilo, Sep 2026).
- **A lift being re-belted after already reaching a later stage is rework, not routine progress** — flag it rather than crediting it as a normal Stage 13 belting entry.
- **Cross-lift part transfers** ("removed parts from lift X, installed on lift Y") happen on multi-lift jobs, usually when one lift is delayed and another needs stock urgently. Log for context; doesn't itself indicate progress on the donor lift.
- **Multi-job days** need the log entry split by job before being fed into any one job's tracker.
- **Bolt/fastener shortages** are a recurring bottleneck across jobs (missing 8mm bolts, Allen key bolts, Z-bracket bolts, etc.), the same delay pattern as Kemset drying time or missing packers — worth watching for as a real, repeatable site issue rather than a one-off.
- **Heavy fabrication load can be its own bottleneck.** At least one site required metal cutting for nearly every component (drive, unistraps, options box, cube, pit ladder boxes, door frame fixings) — a distinct pattern from the hollow-brick-substrate issue, but the same general category of "unusually fabrication-heavy site slows the whole job down."
- **Installer handoffs mid-job happen.** A generic "items list"/pack-up entry near the end of a batch can mean the job is being handed to a different installer, not that it's finished — logs may legitimately resume later under someone else's entries. Don't assume Stage 14 (commissioning) just because a job's logs go quiet or end on a tidy-up note.
- **Occasionally an entry references an entirely different, unrelated job** (wrong-job mislog). These get excluded from the tracker entirely rather than force-fit somewhere. But check company/brand names before assuming this — a related or acquired company (e.g. Liftronic, acquired by Schindler) showing up isn't the same thing as a different job.
- **Tool-access blockers** are their own bottleneck category, distinct from consumable shortages. A job can stall because a needed tool (e.g. a bandsaw) is locked in a colleague's toolbox while that colleague is on a different job.
- **Informal material staging between jobs is normal and not the same as a wrong-job mislog.** An informal staging place name showing up as a materials source/destination on a different job usually just means whichever site had spare space at the time was used for staging — read each case on its actual content, don't treat the place name alone as a red flag.
- **The same real-world event can get logged more than once** — a task spanning multiple days, or logged by two different people. Treat as one continuous piece of work, not double-counted.
