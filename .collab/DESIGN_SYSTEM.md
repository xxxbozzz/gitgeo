# gitgeo Design System — from UI UX Pro Max

## Style: Minimalism & Swiss Modernism
- 12-column grid, mathematical spacing (8px base unit)
- Inter font, weight 400-700
- Single accent color, no decoration
- WCAG AAA contrast
- Clean borders, subtle shadows only when needed
- Tech: Next.js 14 + shadcn/ui + Tailwind

## Color Palette: CRM Professional
Source: UI UX Pro Max colors.csv (B2B CRM)
```
Background:  #F8FAFC
Card:        #FFFFFF
Foreground:  #0F172A
Muted:       #F1F5FD
Muted Text:  #64748B
Border:      #E4ECFC
Primary:     #2563EB
Secondary:   #3B82F6
Accent:      #059669 (green for success)
Destructive: #DC2626
Ring:        #2563EB
```

## Typography
- Font: Inter (400, 500, 600, 700)
- Page title: 1.5rem (700)
- Section header: 1rem (600)
- Body: 0.875rem (400)
- Caption: 0.75rem (500)
- KPI value: 1.75rem (700)

## Components
All from shadcn/ui (Radix primitives):
- Sidebar: Sheet/Command menu pattern
- Cards: border + subtle shadow on hover
- Tables: clean borders, zebra optional
- Forms: floating labels or standard inputs
- Buttons: pill-shaped primary, ghost secondary
- Tags: rounded pill, colored bg
- Charts: ECharts with custom theme
