# Design System

## Subject and Job

The subject is a Kathmandu-based developer building AI systems, developer tools, research platforms, and practical web applications. The profile's single job is to create a memorable first impression while directing visitors toward the pinned repositories below it.

## Visual Thesis

Kathmandu is represented as infrastructure rather than tourism: a network node operating at Nepal Standard Time, set above a compact city silhouette and mountain contour. Repositories become connected services around the central node.

## Signature

`KTM-NP-0545` is the central transmission tower. The `+05:45` timezone is both real information and the identity marker that makes the composition specific to Nepal.

The local review interface extends that signature into a physical-feeling build desk: hard offset shadows, a Kathmandu registration card, workshop labels, and a mint render bay. It is intentionally louder than the GitHub artwork because its job is inspection and presentation, not profile scanning.

## Palette

### Dark

- Night: `#071419`
- Panel: `#0D2026`
- Border: `#28505A`
- Signal mint: `#72E2C4`
- Route cyan: `#59C3DA`
- Beacon amber: `#F0B84B`
- Alert crimson: `#DB5A57`
- Text: `#EAF3F2`
- Muted: `#8DA9AD`

### Light

- Paper sky: `#EDF4F1`
- Panel: `#F8FBF9`
- Border: `#91AAA7`
- Signal mint: `#087D70`
- Route cyan: `#0B748B`
- Beacon amber: `#9B6200`
- Alert crimson: `#B33E3B`
- Text: `#142426`
- Muted: `#536B6D`

## Typography

- Identity: system monospace, bold, 28-34 px.
- Section labels: system monospace, bold, 12-14 px.
- Body and telemetry: system monospace, 13-16 px.
- Preview display: Impact/Arial Narrow, used only for the two-line `KATHMANDU NODE` masthead.
- Preview utility copy: system monospace for controls, coordinates, and build signals.
- No remote font dependency.
- Letter spacing remains zero for body copy; uppercase labels may use restrained positive tracking.

## Layout

```text
+----------------------------------------------------------+
| IDENTITY                              NPT / PUBLIC SIGNAL |
+-------------+----------------------------+---------------+
| CURRENT     |                            | TELEMETRY     |
| BUILD       |       KTM-NP-0545          | latest repo   |
|             |      /    |     \          | stars/repos   |
|             | projects as service nodes | generated at  |
|             |                            |               |
+-------------+----- mountains / city -----+---------------+
| naitik@ktm:~$ building useful and unusual software       |
+----------------------------------------------------------+
```

## Motion

- One beacon pulse at the central node.
- Signal packets move slowly along repository routes.
- One terminal cursor blinks.
- Motion is disabled through `prefers-reduced-motion` where supported.
- The first frame must remain complete and readable.
- The preview can pause SVG animation after inlining the selected repository asset.

## Preview Interface

- Neobrutalist construction: 3 px black rules, square controls, hard 8 px shadows, and no decorative rounded cards.
- Paper, red, blue, yellow, and mint form a workshop palette distinct from the profile artwork's restrained teal system.
- Theme and viewport selectors are true segmented controls.
- Narrow screens select the dedicated mobile artwork automatically.
- The artwork remains the primary object; telemetry and generation controls live in a separate inspector column.

## Content Rules

- Projects use lifecycle labels, not fake uptime.
- Dynamic values are labeled as public GitHub signals.
- No claims of production operation unless a project is actually deployed.
- No generic technology badge wall.
- No duplicate biography or contact section.

## Self-Critique

The initial terminal concept was too close to generic operations dashboards. The revision spends its visual boldness on the Kathmandu infrastructure scene and keeps the surrounding panels restrained. The skyline is meaningful context; the network routes encode actual project relationships; status labels communicate lifecycle rather than decorative telemetry.
