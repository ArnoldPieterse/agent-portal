# Design Tokens — Live Reference (2026-11-16)

Source file: `ui/app.css` :root block. 55 tokens, 436 var() references, 0 hard-coded hexes outside :root.
Extends: memory/portal/ui-tokens.md (original token lineage).

## Surfaces
| Token | Value | Usage |
|-------|-------|-------|
| --bg | #0e1116 | App background |
| --panel | #151a22 | Primary panel bg |
| --panel2 | #1b2230 | Elevated panel bg |
| --line | #2a3342 | Borders, dividers, hover bg |
| --bg-deep | #0d1117 | Queue panel (darker than bg) |
| --peek-bg | #141a26 | File peek popup |
| --acard-sel | #20304d | Selected agent card |
| --you-bg | #243b63 | User message bubble |
| --you-border | #33507f | User message border |

## Text
| Token | Value | Usage |
|-------|-------|-------|
| --text | #e8edf4 | Primary text |
| --dim | #9aa7b8 | Secondary text |
| --faint | #8b98ab | Tertiary / placeholder |
| --busyspan | #8b93a7 | Busy/italic indicator |
| --peek-text | #cdd3e0 | Peek popup body |
| --peek-body | #aab2c5 | Peek code text |
| --qtext | #c9d1d9 | Queue item text |
| --qdim | #8b949e | Queue metadata (ts, count) |

## Accent
| Token | Value | Usage |
|-------|-------|-------|
| --acc | #4f8cff | Primary accent (buttons, links) |
| --acc-hover | #3a6fd6 | Active segment button bg |
| --on-acc | #fff | Text on accent-colored elements |
| --acc-light | #9ccaff | Link hover, peek heading |
| --flink | #6db1ff | File links |

## Status
| Token | Value | Usage |
|-------|-------|-------|
| --ok | #3ddc84 | Success / online |
| --warn | #ff9f43 | Warning / busy |
| --err | #ff6b6b | Error / offline |
| --focus | #7fb0ff | Focus ring color |
| --fdot-idle-gray | #888 | Unknown status dot |
| --fdot-busy | #ffb454 | Busy status dot |
| --fdot-err | #e05252 | Error status dot |

## Banner (interrupt)
| Token | Value | Usage |
|-------|-------|-------|
| --banner-border | #d29922 | Border |
| --banner-bg | #2d2000 | Background |
| --banner-text | #e3b341 | Text |

## DM Segment
| Token | Value | Usage |
|-------|-------|-------|
| --dm-border | #4a3f6b | Border |
| --dm-text | #b79ce0 | Summary label |

## Spinner
| Token | Value | Usage |
|-------|-------|-------|
| --spinner-track | #30363d | Track ring |
| --spinner-fill | #58a6ff | Active arc |

## Peek Popup
| Token | Value | Usage |
|-------|-------|-------|
| --peek-line | #2c3548 | Separators, border |
| --peek-text | #cdd3e0 | Body text |
| --peek-body | #aab2c5 | Code content |

## Radius
| Token | Value | Usage |
|-------|-------|-------|
| --radius-sm | 4px | Small elements (chips) |
| --radius-md | 8px | Buttons, cards, panels (default) |
| --radius-lg | 12px | Large panels, modals |

## Shadow
| Token | Value | Usage |
|-------|-------|-------|
| --shadow-lg | 0 8px 24px rgba(0,0,0,.5) | Peek popup, elevated cards |

## Motion
| Token | Value | Usage |
|-------|-------|-------|
| --dur-fast | .1s | Subtle state changes |
| --dur-med | .15s | Standard transitions (hover, color) |
| --dur-slow | .2s | Dot/status transitions |

## Spacing
| Token | Value |
|-------|-------|
| --sp-4 | 4px |
| --sp-8 | 8px |
| --sp-12 | 12px |
| --sp-16 | 16px |
| --sp-24 | 24px |

## Type Scale
| Token | Value |
|-------|-------|
| --fs-11 | 11px (labels, metadata) |
| --fs-12 | 12px (chips, small) |
| --fs-13 | 13px (body compact) |
| --fs-14 | 14px (body default) |
| --fs-15 | 15px (emphasized body) |
| --fs-16 | 16px (headings) |

---
Verification: `grep -c 'var(--' ui/app.css` = 436; `grep -oP '#[0-9a-fA-F]{3,8}' ui/app.css | grep -v ':root' | wc -l` = 0.
