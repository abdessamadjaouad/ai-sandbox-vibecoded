# AI Sandbox — Frontend Design System & Interface Specification

## Purpose
This document is a precise blueprint for recreating the AI Sandbox frontend interfaces in Figma. It contains every color, font, spacing value, component specification, and page layout needed to produce pixel-perfect designs.

---

## 1. Global Design Tokens

### 1.1 Fonts
- **Primary (Body / UI):** IBM Plex Sans, weights 400, 500, 600, 700
- **Display (Headings):** Playfair Display, weights 600, 700
- **Fallback stack:** -apple-system, BlinkMacSystemFont, sans-serif
- **Monospace (Metric values):** IBM Plex Sans (monospace style used for numbers)

### 1.2 Color Palette — Light Mode (`:root` or `data-theme="light"`)

| Token | Value | Usage |
|---|---|---|
| `--dxc-amber` | `#ffb372` | Brand accent, gradient start |
| `--dxc-coral` | `#ff784e` | Brand accent, active states, eyebrow text |
| `--dxc-blue` | `#569af4` | Brand accent, links, focus rings, primary actions |
| `--dxc-purple` | `#8b7cf6` | Brand accent, gradient middle |
| `--success` | `#22c58b` | Success states, completed steps |
| `--success-soft` | `rgba(34,197,139,0.12)` | Success backgrounds |
| `--error` | `#ef4444` | Error states, failed experiments |
| `--error-soft` | `rgba(239,68,68,0.1)` | Error backgrounds |
| `--warning` | `#f59e0b` | Warning states, pending/running |
| `--warning-soft` | `rgba(245,158,11,0.12)` | Warning backgrounds |
| `--bg` | `#f6f3ef` | Page background (warm off-white) |
| `--bg-pattern` | `#ebe8e2` | Subtle pattern backgrounds |
| `--surface` | `#ffffff` | Card backgrounds |
| `--surface-elevated` | `#ffffff` | Elevated surfaces |
| `--surface-muted` | `#f6f3ef` | Muted surfaces (table headers) |
| `--surface-interactive` | `#e8e4dc` | Hover states, interactive backgrounds |
| `--surface-brand` | `rgba(86,154,244,0.06)` | Brand-tinted surfaces |
| `--ink` | `#0f172a` | Primary text |
| `--ink-secondary` | `#475569` | Secondary text |
| `--ink-muted` | `#64748b` | Muted text, placeholders |
| `--ink-subtle` | `#94a3b8` | Very subtle text |
| `--ink-inverse` | `#f8fafc` | Text on dark backgrounds |
| `--border` | `rgba(15,23,42,0.08)` | Default borders |
| `--border-strong` | `rgba(15,23,42,0.15)` | Stronger borders |
| `--border-brand` | `rgba(86,154,244,0.3)` | Brand-colored borders |
| `--border-warm` | `rgba(255,120,78,0.25)` | Warm accent borders |

### 1.3 Color Palette — Dark Mode (`data-theme="dark"`)

| Token | Value | Usage |
|---|---|---|
| `--bg` | `#0a0e17` | Page background (deep navy/black) |
| `--bg-pattern` | `#0f1520` | Subtle pattern backgrounds |
| `--surface` | `#131a27` | Card backgrounds |
| `--surface-elevated` | `#1a2235` | Elevated surfaces |
| `--surface-muted` | `#0f1520` | Muted surfaces |
| `--surface-interactive` | `#1e2738` | Hover states |
| `--surface-brand` | `rgba(86,154,244,0.08)` | Brand-tinted surfaces |
| `--ink` | `#f1f5f9` | Primary text (off-white) |
| `--ink-secondary` | `#cbd5e1` | Secondary text |
| `--ink-muted` | `#94a3b8` | Muted text |
| `--ink-subtle` | `#64748b` | Very subtle text |
| `--ink-inverse` | `#0f172a` | Text on light backgrounds |
| `--border` | `rgba(241,245,249,0.08)` | Default borders |
| `--border-strong` | `rgba(241,245,249,0.15)` | Stronger borders |
| `--border-brand` | `rgba(86,154,244,0.35)` | Brand-colored borders |
| `--border-warm` | `rgba(255,120,78,0.3)` | Warm accent borders |

### 1.4 Gradients

| Name | Value | Usage |
|---|---|---|
| Brand gradient | `linear-gradient(135deg, #ffb372 0%, #ff784e 40%, #569af4 100%)` | Hero text, active step numbers, score bars, CTAs |
| Brand gradient subtle | `linear-gradient(135deg, rgba(255,179,114,0.15) 0%, rgba(255,120,78,0.12) 40%, rgba(86,154,244,0.18) 100%)` | Hero decorative background |
| Blue gradient | `linear-gradient(145deg, #569af4 0%, #3b82f6 100%)` | Blue accent buttons |
| Warm gradient | `linear-gradient(145deg, #ffb372 0%, #ff784e 100%)` | Warm accent elements |
| Dark gradient (light mode) | `linear-gradient(180deg, #1a1f2e 0%, #0f1219 100%)` | Primary button backgrounds |
| Dark gradient (dark mode) | `linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%)` | Primary button backgrounds |
| Surface gradient (light) | `linear-gradient(180deg, rgba(255,255,255,0.95) 0%, rgba(248,250,255,0.9) 100%)` | Glass card backgrounds |
| Surface gradient (dark) | `linear-gradient(180deg, rgba(19,26,39,0.98) 0%, rgba(15,21,32,0.95) 100%)` | Glass card backgrounds |
| Score gradient | `linear-gradient(90deg, #569af4 0%, #8b7cf6 35%, #ff784e 70%, #ffb372 100%)` | Score bar fills |

### 1.5 Shadows

| Name | Value | Usage |
|---|---|---|
| `--shadow-xs` | `0 1px 2px rgba(15,23,42,0.05)` | Minimal elevation |
| `--shadow-sm` | `0 2px 8px rgba(15,23,42,0.06), 0 1px 2px rgba(15,23,42,0.04)` | Small cards |
| `--shadow-md` | `0 8px 24px rgba(15,23,42,0.08), 0 2px 8px rgba(15,23,42,0.04)` | Default cards |
| `--shadow-lg` | `0 16px 48px rgba(15,23,42,0.1), 0 8px 16px rgba(15,23,42,0.06)` | Elevated cards |
| `--shadow-xl` | `0 24px 64px rgba(15,23,42,0.14), 0 12px 24px rgba(15,23,42,0.08)` | Modals, dialogs |
| `--shadow-brand` | `0 8px 32px rgba(86,154,244,0.2), 0 4px 12px rgba(86,154,244,0.1)` | Brand elevation |
| `--shadow-warm` | `0 8px 32px rgba(255,120,78,0.15)` | Warm elevation |

**Dark mode shadows** use higher opacity black values (see CSS file for exact dark variants).

### 1.6 Spacing Scale

| Token | Value |
|---|---|
| `--space-xs` | `0.25rem` (4px) |
| `--space-sm` | `0.5rem` (8px) |
| `--space-md` | `1rem` (16px) |
| `--space-lg` | `1.5rem` (24px) |
| `--space-xl` | `2rem` (32px) |
| `--space-2xl` | `3rem` (48px) |
| `--space-3xl` | `4rem` (64px) |

### 1.7 Border Radius

| Token | Value |
|---|---|
| `--radius-sm` | `6px` |
| `--radius-md` | `10px` |
| `--radius-lg` | `16px` |
| `--radius-xl` | `24px` |
| `--radius-2xl` | `32px` |
| `--radius-full` | `9999px` (pill shape) |

### 1.8 Typography Scale

| Token | Size | Usage |
|---|---|---|
| `--text-xs` | `0.75rem` (12px) | Labels, tags, captions |
| `--text-sm` | `0.875rem` (14px) | Body secondary, form labels |
| `--text-base` | `1rem` (16px) | Default body text |
| `--text-lg` | `1.125rem` (18px) | Lead paragraphs |
| `--text-xl` | `1.25rem` (20px) | Small headings |
| `--text-2xl` | `1.5rem` (24px) | Section headings |
| `--text-3xl` | `2rem` (32px) | Large headings |
| `--text-4xl` | `2.5rem` (40px) | Hero sub-headings |
| `--text-5xl` | `3.25rem` (52px) | Hero headings |

### 1.9 Global Background

The page background in light mode is a warm off-white (`#f6f3ef`) with three layered radial gradients fixed to the viewport:
1. Top-left: amber tint (`rgba(255,179,114,0.08)`)
2. Top-right: blue tint (`rgba(86,154,244,0.1)`)
3. Bottom-center: coral tint (`rgba(255,120,78,0.06)`)

---

## 2. Component Specifications

### 2.1 Buttons

All buttons use `border-radius: var(--radius-full)` (pill shape).

**Primary Button (`.btn-primary`)**
- Light mode: Dark gradient background (`#1a1f2e` → `#0f1219`), white text (`#f8fafc`)
- Dark mode: Light gradient background (`#f8fafc` → `#e2e8f0`), dark text (`#0f172a`)
- Padding: `0.75rem 1.5rem`
- Font: IBM Plex Sans, 14px, weight 600
- Shadow: `0 4px 16px rgba(15,23,42,0.25)` (light) / `0 4px 16px rgba(255,255,255,0.1)` (dark)
- Hover: translateY(-2px), larger shadow
- Disabled: opacity 0.5, no transform

**Ghost Button (`.btn-ghost`)**
- Background: transparent
- Border: `1px solid var(--border-strong)`
- Text: `--ink-secondary`
- Hover: `--surface-interactive` background, `--border-brand` border

**Brand Button (`.btn-brand`)**
- Background: Brand gradient (`#ffb372` → `#ff784e` → `#569af4`)
- Text: white
- Shadow: `--shadow-warm`
- Hover: translateY(-2px) scale(1.02), larger warm shadow
- Used for the main CTA on the landing page

**Size Variants**
- `.btn-sm`: `0.5rem 1rem`, 12px font
- `.btn-lg`: `1rem 2rem`, 16px font

### 2.2 Glass Card (`.glass-card`)

- Background: `--surface-gradient` (white-to-blue-tint in light, dark navy in dark)
- Border: `1px solid var(--border)`
- Border radius: `--radius-xl` (24px)
- Box shadow: `--shadow-md`
- Padding: `--space-xl` (2rem)
- Backdrop filter: `blur(12px)`
- **Special border effect:** A pseudo-element creates a 1px gradient border (white → transparent → blue) using mask-composite. This gives the card a subtle sheen on its edge.

### 2.3 Form Inputs

- Width: 100%
- Padding: `0.75rem 1rem`
- Background: `--surface`
- Border: `1px solid var(--border-strong)`
- Border radius: `--radius-md` (10px)
- Text: `--ink`
- Focus: Border color `--dxc-blue`, box-shadow `0 0 0 3px rgba(86,154,244,0.15)`
- Placeholder: `--ink-subtle`

**Labels**
- Display: flex column
- Gap: `--space-xs`
- Font: 14px, weight 500, color `--ink-secondary`

### 2.4 Status Tags

Small inline badges for experiment/model status:
- `.status-tag.is-completed`: Background `--success-soft`, text `--success`
- `.status-tag.is-failed`: Background `--error-soft`, text `--error`
- `.status-tag.is-pending` / `.is-running`: Background `--warning-soft`, text `--warning`
- Border radius: `--radius-full`
- Padding: `2px 10px`
- Font: 12px, weight 500, uppercase

### 2.5 Chips (`.chip`)

- Padding: `var(--space-xs) var(--space-md)`
- Background: `--surface`
- Border: `1px solid var(--border)`
- Border radius: `--radius-full`
- Font: 14px, color `--ink-secondary`
- Hover: `--border-brand`
- Active (`.is-active`): `--surface-brand` background, `--dxc-blue` border, `--ink` text

### 2.6 Spinner Panel

- Centered flex container
- Contains a `.spinner` (animated rotating circle) + text below
- Used for loading states inside cards

### 2.7 Score Bars

- Track: height 10px, `--surface-interactive` background, `--radius-full`
- Fill: `--score-gradient` (blue → purple → coral → amber), `--radius-full`
- Label row: Flex between, model name left, score right
- Best row (`.is-best`): Model name and score in brand color

---

## 3. Shared Layout Components

### 3.1 Navbar (`.navbar`)

- Fixed/sticky at top
- Full width, max-width `--max-content` (1400px) centered
- Height: ~64px
- Background: `--surface` with subtle blur
- Layout: 3 zones (left: brand, center: links, right: actions)
- **Left:** DXC logo (52px) + "AI Sandbox" text + "Enterprise Benchmark Studio" tagline
- **Center links:** Home, About Us, My Experiments (if logged in), API Docs / MLflow (if admin)
- Links are text buttons; active link has underline/highlight
- **Right:** Theme toggle (moon/sun icon), user name + Logout button (if authenticated) OR Login / Sign Up buttons (if anonymous)
- **Mobile:** Hamburger menu that expands a dropdown

### 3.2 Footer (`.footer`)

- Full width, dark background in light mode (`--dark-gradient`)
- 5-column grid layout on desktop:
  1. Brand column: DXC logo SVG (gradient from amber to blue), tagline "IMPOSSIBLE. DELIVERED."
  2. Company: About Us, Leadership, Corporate Responsibility
  3. Resources: Documentation, API Reference, Support
  4. Legal: Privacy Policy, Terms of Service, Cookie Policy
  5. Contact: Contact Us, Careers, DXC.com
- Bottom bar: "© YEAR DXC Technology Company. All rights reserved." + "AI Sandbox is a project by DXC Technology & ENSAM Casablanca"
- Links are light gray text, hover to white
- Responsive: stacks to single column on mobile

### 3.3 Wizard Shell

When the user enters the wizard flow, the layout changes:

**Wizard Header (`.wizard-header`)**
- Flex row: brand inline (logo + "AI Sandbox" + "Benchmark Wizard") | step navigation | Exit button
- Background: `--surface`, border `--border`, radius `--radius-xl`, shadow `--shadow-sm`
- Step navigation: 5 pill buttons in a row
  - Each step shows a numbered circle (26px) + label
  - Active step: `--surface-brand` background, `--border-brand` border, number has brand gradient background with white text
  - Completed step: number has `--success` background with white checkmark
  - Future steps: muted text, disabled

**Wizard Body (`.wizard-body`)**
- Flex: 1 (fills available space)
- Background: `--surface`, border `--border`, radius `--radius-2xl` (32px), shadow `--shadow-md`
- Padding: `--space-2xl` (3rem)
- Overflow: auto

**Wizard Footer (`.wizard-footer`)**
- Flex row: Back button | progress bar | Continue button
- Background: `--surface`, border `--border`, radius `--radius-xl`, shadow `--shadow-sm`
- Progress bar: 8px height, `--surface-interactive` track, `--brand-gradient` fill, `--radius-full`
- Back: `.btn-ghost`, disabled on step 1
- Continue: `.btn-primary`, disabled when step validation fails

---

## 4. Page Specifications

### 4.1 Signup Page (Default landing for unauthenticated users)

**Layout:** Full-screen split layout (desktop)
- **Left (60%):** White/light form area
- **Right (40%):** Dark gradient decorative panel with brand content

**Left Panel — Form Card (`.auth-card`)**
- Glass card styling
- Header: "Create Account" (Playfair Display, 2xl) + "Join AI Sandbox to start benchmarking" (muted)
- Form fields (stacked vertically, gap 1rem):
  - Full Name (optional): text input
  - Username *: text input, min 3 chars
  - Email *: email input
  - Password *: password input, min 8 chars
  - Confirm Password *: password input
  - Terms checkbox: "I agree to the Terms of Service and Privacy Policy"
- Submit button: `.btn-primary` full width, "Create Account"
- Loading state: spinner + "Creating account..."
- Footer link: "Already have an account? Sign in"
- Error display: Red banner with alert icon + message

**Success State**
- Large checkmark icon (coral/brand color)
- "Welcome!" heading
- Success message + "Continue to Dashboard" button

**Right Panel — Decoration (`.auth-decoration`)**
- Background: `--dark-gradient` or brand gradient
- Content centered vertically:
  - "AI Sandbox" heading (white, Playfair Display)
  - Subtitle paragraph
  - Feature list with checkmark icons:
    - Multi-model comparison
    - Automated benchmarking
    - Detailed reports & analytics
    - Enterprise governance

**Mobile:** Stack vertically, decoration panel hidden or moved to top.

### 4.2 Login Page

- Same split layout as Signup
- Form fields:
  - Username *: text input
  - Password *: password input
  - "Remember me" checkbox
  - "Forgot password?" link (right aligned)
- Submit: "Sign In"
- Footer: "Don't have an account? Sign up"
- Right panel identical to Signup

### 4.3 Landing Page (for authenticated users)

**Layout:** Single column, max-width 1400px, centered.

**Hero Section (`.hero`)**
- `.glass-card` with extra padding (`--space-3xl` vertical, `--space-2xl` horizontal)
- Min-height: 420px
- Decorative pseudo-elements:
  - Top-right: large rotated rectangle with `--brand-gradient-subtle` (creates a soft glow)
  - Bottom: 1px horizontal line with brand gradient (blue → coral), 30% opacity
- Content (left-aligned):
  - Eyebrow: "Enterprise AI Benchmark Studio" (coral, uppercase, letter-spacing 0.12em)
  - H1: "Benchmark AI models in minutes, **with governance built in.**" (second half uses `.text-gradient`)
    - Font: Playfair Display, clamp(2rem, 5vw, 3.25rem)
    - Max-width: 16ch
  - Paragraph: Description text, `--ink-secondary`, max-width 65ch
  - CTA row (flex, gap 1rem):
    - Primary: `.btn-brand.btn-lg` — "Start Benchmark Wizard"
    - Secondary: `.btn-ghost.btn-lg` — "Learn About DXC" (external link)
  - Meta line: "**{count}** datasets ready for benchmarking"

**Feature Grid (`.landing-grid`)**
- 3-column grid, gap `--space-lg`
- Each card: `.glass-card.feature-card`
  - Top border accent: 4px brand gradient line (hidden by default, visible on hover)
  - Hover: translateY(-6px), `--shadow-lg`, `--border-brand`
  - H3: IBM Plex Sans, 18px, weight 600. Title has a small 8px brand-gradient square dot before it.
  - List items: 14px, `--ink-secondary`. Each item has a coral "→" arrow prefix.

**Cards content:**
1. "What AI Sandbox Provides" — 4 bullet points about validation, catalogue, tracking, reports
2. "Built for Regulated Industries" — 4 bullet points about banking, insurance, public sector, non-technical users
3. "Comprehensive Evaluation" — 4 bullet points about tabular ML, NLP/LLM, RAG, agent evaluation

### 4.4 About Page

**Layout:** Single column, max-width 1400px, centered, gap `--space-xl` between sections.

**Hero Section (`.about-hero`)**
- Eyebrow: "About DXC Technology"
- H1: "Driving **Digital Transformation** Worldwide" ("Digital Transformation" uses `.text-gradient`)
- Lead paragraph: `--ink-secondary`, max-width 65ch

**About Grid (`.about-grid`)**
- 4-column grid of `.glass-card.about-card`
- Each card has:
  - Large icon (48px stroke icon) in brand color
  - H3: IBM Plex Sans, 18px, weight 600
  - Paragraph: 14px, `--ink-secondary`
- Topics: Global Presence, Technology Leadership, Our People, Commitment to Excellence

**Mission Section**
- `.glass-card` centered
- H2: "Our Mission"
- Blockquote: large italic text in Playfair Display

**Project Section**
- Header: "AI Sandbox Project" + subtitle "A collaboration between DXC Technology and ENSAM Casablanca"
- Project card:
  - Logo + "PFE Project" badge (brand gradient text)
  - Intro paragraph
  - **Capability Grid:** 4 items with emoji icons:
    - 📊 Tabular ML
    - 📝 NLP/LLM
    - 🔍 RAG
    - 🤖 Agent Evaluation
  - **Sector Tags:** Finance, Banking, Insurance, Public Sector (pill chips)

**Stats Section (`.about-stats`)**
- 4-column grid of stat blocks
- Large number (Playfair Display, 2.5rem, weight 700) + label (14px, muted)
- Values: 70+ Countries, 130K+ Employees, 6,000 Customers, $14B+ Revenue

**CTA Section**
- `.glass-card`
- H2 + paragraph + 2 buttons (Primary: "Visit DXC.com", Ghost: "Contact Us")

### 4.5 History Page ("My Experiments")

**Layout:** Single column with internal 2-column grid (list + details).

**Header (`.history-header`)**
- `.glass-card`
- Left: H1 "My Experiments" + "Manage your benchmark runs"
- Right: 3 stat pills (Total, Completed, Failed) with large numbers

**Toolbar (`.history-toolbar`)**
- `.glass-card`
- Left: Search box with magnifying glass icon, placeholder "Search experiments..."
- Right: 2 dropdown filters:
  - Type: All Types, Tabular ML, NLP, LLM, RAG, Agent
  - Sort: Newest First, Oldest First, Name, Status

**Content Grid (`.history-content`)**
- 2 columns (1fr 1fr), gap `--space-lg`
- Responsive: single column below 1100px

**Left: Experiments List**
- Grid of `.experiment-card.glass-card`
  - Auto-fill, minmax 280px
  - Hover: translateY(-2px), shadow
  - Selected: `--dxc-coral` border
  - Header row: Type badge (blue background pill) + Status text (colored)
  - Title: 16px, weight 600
  - Date: 13px, muted
  - Task type tag: small muted pill

**Right: Details Panel (`.experiment-details`)**
- Sticky, top `--space-lg`
- Max-height: `calc(100vh - 200px)`, overflow auto
- Empty state: Icon + "Select an experiment to view details"
- Loading state: Spinner + "Loading details..."
- Content when selected:
  - Type badge + H2 title + description + date
  - **Stats grid:** 5 stat cards
    - Status (colored)
    - Models (count)
    - Success (green)
    - Failed (red)
    - Best Model (spans 2 columns, brand gradient background, shows model name + score)
  - **Recommendation box:** H4 + paragraph
  - **Action:** `.btn-brand` "View Full Report"

### 4.6 Wizard Step 1 — Upload Data

**Step header:**
- Eyebrow: "Step 1"
- H2: "Upload your dataset once"
- Subtitle: "Add a CSV, JSON, Parquet, or Excel file. We detect the dataset name, target column, task type, and features automatically."

**Layout:** 2-column grid (`.grid-two`)

**Left: Upload Form (`.form-card.glass-card`)**
- H3: "New upload"
- Dataset name: text input (auto-filled from filename, editable)
- Muted helper: "The name is auto-detected from the file. You can edit it any time."
- Description: textarea, 4 rows
- File input: accept `.csv,.json,.jsonl,.parquet,.xlsx,.xls`
- Submit: `.btn-primary` "Upload and Auto-Configure"

**Right: Dataset List (`.dataset-card.glass-card`)**
- H3: "Available datasets"
- Loading: SpinnerPanel
- Empty: "No datasets yet. Upload your first file."
- List: vertical stack of `.dataset-list__item`
  - Each item: flex row, space-between
  - Left: Name (bold) + Row/column count (small, muted)
  - Right: Status tag (small pill)
  - Hover: translateX(4px), `--border-brand`, `--shadow-sm`
  - Active (selected): `--dxc-coral` border, brand-tinted background, warm shadow

**Bottom: Preview Card (`.preview-card.glass-card`)** — shown when dataset selected
- H3: "Auto-detected preview"
- List: Rows, Columns, Quality check, Detected task type

### 4.7 Wizard Step 2 — Create Split

**Step header:**
- Eyebrow: "Step 2"
- H2: "Create benchmark-ready split"
- Subtitle: "Use the recommended split to continue fast. Open advanced settings only if you want to tune technical options."

**Layout:** 2-column grid

**Left: Configuration Form (`.form-card.glass-card`)**
- H3: "Recommended configuration"
- Meta line: "Task type: {type} · Train 70% · Validation 15%, Test 15%"
- Primary button: "Create Recommended Split"
- **Advanced Panel (`.advanced-panel`)** — collapsible `<details>` element
  - Border: `--border-warm`
  - Background: `rgba(255,120,78,0.03)`
  - Summary: "Advanced settings" with ▸ icon (rotates 90° when open)
  - Controls:
    - Train ratio slider (0.5–0.9, step 0.05)
    - Validation ratio slider (0–0.4)
    - Test ratio slider (0–0.4)
    - Random seed number input
    - Stratify column dropdown (optional)
  - Validation: Total ratio must equal 1.0 (shown below)

**Right: Versions List (`.dataset-card.glass-card`)**
- H3: "Existing versions"
- List items: "Version {N}" + train/val/test row counts + "ready" badge
- Same active/hover states as dataset list

### 4.8 Wizard Step 3 — Review Models

**Step header:**
- Eyebrow: "Step 3"
- H2: "Review detected setup and models"
- Subtitle: "Everything is pre-selected for you. Adjust only if needed."

**Confidence Card (`.confidence-card`)** — shown when auto-config exists
- Background: `--surface-brand`, border: `--border-brand`
- Text: "Auto-detection: {rationale}"
- Muted line: "Detected task type: {type} · Confidence: {level}"

**Layout:** 2-column grid

**Left: Prediction Setup (`.form-card.glass-card`)**
- H3: "Prediction setup"
- Target column: `<select>` dropdown with all columns
- Feature columns: `<fieldset>` with legend
  - `.chip-grid`: flex wrap of `.chip` buttons
  - One chip per column (excluding target)
  - Active chips: `--surface-brand` background, `--dxc-blue` border

**Right: Model Catalogue (`.dataset-card.glass-card`)**
- Header row (`.model-catalogue-header`): H3 "Model catalogue" + "Select all" checkbox
- Model list: vertical stack of `.model-list__item`
  - Grid: auto | 1fr | auto
  - Checkbox (18px, accent `--dxc-coral`)
  - Model name (bold) + description (small, muted)
  - Family tag (small uppercase pill, `--surface-interactive` background)
  - Selected state: `--dxc-coral` border, brand-tinted background

### 4.9 Wizard Step 4 — Run Benchmark

**Step header:**
- Eyebrow: "Step 4"
- H2: "Launch sandbox run"
- Subtitle: "Start the experiment. We train each selected model and rank them automatically."

**Layout:** 2-column grid

**Left: Run Setup Form (`.form-card.glass-card`)**
- H3: "Run setup"
- Experiment name: text input (pre-filled from auto-config)
- Description: textarea, 4 rows
- Random seed: number input
- Submit button: `.btn-primary`
  - States: "Create and Run" (idle) / "Running..." (processing) / "Run Again" (completed) / "Retry Run" (failed)
  - Shows `.btn-spinner` during processing
- Success hint: Green checkmark icon + "Experiment completed successfully..." (only when completed)

**Right: Run Monitor (`.dataset-card.glass-card`)**
- H3: "Run monitor"
- Loading: SpinnerPanel with progress message
- Experiment details when created:
  - Status badge (colored)
  - Experiment ID (truncated, monospace)
  - Selected models count
  - Started / Completed timestamps
- Error state (`.run-error`):
  - Error message in red
  - Retry button: `.btn-ghost` with refresh icon
- Selected models: `.chip-grid` of active chips

**Experiment Lifecycle States:**
- `idle`: No run started
- `creating`: Creating experiment record
- `running`: Training models
- `polling`: Waiting for completion (auto-polls every 1s, up to 120 attempts)
- `completed`: Success → auto-advances to Step 5
- `failed`: Error message shown, retry available

### 4.10 Wizard Step 5 — Dashboard & Report

**Step header:**
- Eyebrow: "Step 5"
- H2: "Benchmark dashboard and report"
- Subtitle: "Understand which model is recommended and why in plain language."

**Recommendation Callout (`.report-callout.report-callout--branded`)**
- Background: blue-to-purple tinted gradient
- Border: `--border-brand`
- Eyebrow: "Recommendation"
- H3: The recommendation text (Playfair Display, 20px, max-width 50ch)
- Details line: "Best model: **{name}** · Score: **{score}**" (brand-colored bold)

**Global Score Comparison (`.chart-card.glass-card`)**
- H3: "Global score comparison"
- `.score-bars`: vertical stack of `.score-bar-row`
  - Each row:
    - Meta row: Model name (bold) + Score (monospace)
    - Track: 10px height, full width
    - Fill: width proportional to max score, `--score-gradient`
  - Best row: name and score in brand color, fill same gradient

**Model Ranking Table (`.table-card.glass-card`)**
- Header row: H3 "Model ranking" + metric toggle chips
- Table (full width, collapsible columns on small screens):
  - Columns: Rank, Model, Global Score, [Visible Metrics…], Latency (ms), Training (s), Status
  - Header row: 12px, uppercase, letter-spacing 0.05em, `--ink-muted`, `--surface-muted` background
  - Best row: highlighted with brand text color
  - Rank 1: special badge with best styling
  - Status: `.status-tag` (ok = green, failed = red)
- **Metric toggles:** Chip buttons above table to show/hide individual metrics (Accuracy, F1, Precision, Recall, MAE, RMSE, R², etc.)

**Detailed Report (`.markdown-card.glass-card`)**
- Collapsible (default expanded)
- Header: Toggle chevron + "Detailed Report" + action buttons
- Actions (right-aligned):
  - `.btn-ghost`: Markdown download (with download icon)
  - `.btn-primary`: PDF export (with file icon)
- Content: `.markdown-render`
  - White/light background, `--border`, padding `--space-lg`
  - Rendered Markdown (headings, paragraphs, lists, tables, code blocks)
  - Uses ReactMarkdown with remark-gfm for GitHub-flavored markdown

---

## 5. Responsive Behavior

- **Desktop (>= 1100px):** Full layouts as described. 2-column grids, side-by-side panels.
- **Tablet (768px–1099px):** 2-column grids may collapse to single column. History page becomes single column. Navbar shows hamburger menu.
- **Mobile (< 768px):** All grids single column. Wizard header steps show only numbers (labels hidden). Footer stacks to single column. Auth pages stack vertically (decoration panel hidden or minimal).

---

## 6. Animation & Motion

| Animation | Trigger | Details |
|---|---|---|
| Hero fade-in | Page load | Opacity 0→1, translateY(20px→0), duration 0.8s, ease-out. Staggered delays: title 0s, subtitle 0.1s, CTAs 0.2s, meta 0.3s |
| Step reveal | Step change | Opacity 0→1, translateY(12px→0), duration 0.4s, ease-out |
| Card hover | Mouse enter | translateY(-6px), shadow increase, border color change. Duration 0.25s ease-out |
| Button hover | Mouse enter | translateY(-2px), shadow increase. Duration 0.25s |
| Progress bar | Step change | Width transition, duration 0.4s ease-out |
| Score bar fill | Data load | Width from 0% to target, duration 0.4s ease-out |
| Spinner | Loading | Rotating border animation, 1s linear infinite |

---

## 7. Accessibility Requirements

- All buttons must have `type="button"` unless submitting a form
- Form inputs must have associated `<label>` elements with `htmlFor`
- Wizard steps must have `aria-label="Wizard progress"`
- Loading spinners must have `role="status"` and `aria-live="polite"`
- Theme toggle must have `aria-label` describing the action
- Mobile menu toggle must have `aria-expanded`
- Report toggle must have `aria-expanded`
- Color contrast must meet WCAG AA for all text

---

## 8. Assets & Logos

- **DXC Logo:** `frontend/dxc-logo.png` — square brand mark used in navbar, wizard header, about page
- **DXC Glow:** `frontend/dxc-glow.png` — decorative glow asset used on landing page hero
- **Footer Logo:** Inline SVG with radial gradient (amber `#FFB87E` → coral `#FF7E51` → blue `#6399F0`)
- **Favicon:** Derived from DXC logo

---

## 9. File Structure for Reference

```
frontend/src/
  App.tsx              → Root router, state management, API orchestration
  main.tsx             → ReactDOM.createRoot entrypoint
  styles.css           → Complete design system (3400+ lines)
  types.ts             → Shared TypeScript interfaces
  store/
    wizardStore.ts     → Wizard step state + draft data
  context/
    AuthContext.tsx    → JWT auth, login/register/logout
  hooks/
    useApi.ts          → Backend API client (fetch wrapper)
    useWizardExperience.ts → Wizard UX helpers
  components/
    Navbar.tsx         → Top navigation bar
    Footer.tsx         → Site footer
    SpinnerPanel.tsx   → Loading spinner with text
    ProgressRail.tsx   → Wizard sidebar progress (unused in current layout)
    ActionBar.tsx      → Wizard back/next footer (unused in current layout)
  pages/
    LandingPage.tsx    → Marketing landing page
    LoginPage.tsx      → Authentication login
    SignupPage.tsx     → Authentication registration
    AboutPage.tsx      → DXC / project information
    HistoryPage.tsx    → Experiment history + details
    Step1UploadPage.tsx     → Dataset upload/selection
    Step2VersionPage.tsx    → Train/val/test split creation
    Step3ModelPage.tsx      → Target/features/model selection
    Step4RunPage.tsx        → Experiment launch + monitoring
    Step5ReportPage.tsx     → Results dashboard + report export
```

---

## 10. Key Implementation Notes for Figma

1. **Glassmorphism:** Cards use `backdrop-filter: blur(12px)` with semi-transparent gradient backgrounds. In Figma, use layer blur + semi-transparent fills.
2. **Gradient borders:** The `.glass-card::before` pseudo-element creates a 1px gradient border. In Figma, use a stroke with linear gradient.
3. **Page background:** Do not use a flat color. Use the warm off-white `#f6f3ef` with three large soft radial gradients positioned at top-left, top-right, and bottom-center.
4. **Pill shapes:** Every button uses `border-radius: 9999px`. There are no sharp-cornered buttons.
5. **Typography hierarchy:** Headings always use Playfair Display. Body/UI text always uses IBM Plex Sans. Never mix these rules.
6. **Dark mode:** The entire UI inverts — dark backgrounds become light, light surfaces become dark navy, and the primary button flips from dark gradient to light gradient.
7. **Status colors:** Completed = green `#22c58b`, Failed = red `#ef4444`, Running/Pending = amber `#f59e0b`. These are consistent across all pages.
8. **Spacing rhythm:** The design uses a consistent 8px-based spacing system. Most gaps are 8px, 16px, 24px, or 32px.
