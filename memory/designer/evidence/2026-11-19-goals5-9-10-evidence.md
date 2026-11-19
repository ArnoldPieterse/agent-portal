# Designer goals 5/9/10 - acceptance evidence (2026-11-19)

Headless Edge battery (fresh profiles, virtual-time-budget 25s).

## Goal 5 density
- tokens: lh base 1.45->1.3, loose 1.5->1.35, caption 1.3->1.25
- files rows single-line flex+ellipsis; li padding sp-4->sp-3; frow-h sp-8->sp-6

| panel | before px | after px | reduction % |
|---|---|---|---|
| fleetBody | 262 | 235 | 10.3 |
| goalsBody | 288 | 246 | 14.6 |
| filesList | 101641 | 45210 | 55.5 |
body scrollHeight reduction: -1.4%
typography violations: 0 (target 0)

## Goal 9 onboarding tour
- first visit overlay+steps: True
- second visit hidden after flag: True

## Goal 10 print stylesheet
- PDF bytes: 438739
- screenshots: before 96352 B / after 110673 B

Selftest extras - empty_state: {'has_svg_icon': True, 'has_cta_button': True} | notifications: {'toasts': 3, 'badge': '3', 'panel_items': 3}
