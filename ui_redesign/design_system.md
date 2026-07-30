---
name: Streamline Logic
colors:
  surface: '#faf8ff'
  surface-dim: '#d8d9e6'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f3ff'
  surface-container: '#ecedfa'
  surface-container-high: '#e6e7f4'
  surface-container-highest: '#e1e2ee'
  on-surface: '#191b24'
  on-surface-variant: '#424656'
  inverse-surface: '#2e303a'
  inverse-on-surface: '#eff0fd'
  outline: '#727687'
  outline-variant: '#c2c6d8'
  surface-tint: '#0054d6'
  primary: '#0050cb'
  on-primary: '#ffffff'
  primary-container: '#0066ff'
  on-primary-container: '#f8f7ff'
  inverse-primary: '#b3c5ff'
  secondary: '#526069'
  on-secondary: '#ffffff'
  secondary-container: '#d3e2ed'
  on-secondary-container: '#56656e'
  tertiary: '#a33200'
  on-tertiary: '#ffffff'
  tertiary-container: '#cc4204'
  on-tertiary-container: '#fff6f4'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae1ff'
  primary-fixed-dim: '#b3c5ff'
  on-primary-fixed: '#001849'
  on-primary-fixed-variant: '#003fa4'
  secondary-fixed: '#d6e5ef'
  secondary-fixed-dim: '#bac9d3'
  on-secondary-fixed: '#0f1d25'
  on-secondary-fixed-variant: '#3b4951'
  tertiary-fixed: '#ffdbd0'
  tertiary-fixed-dim: '#ffb59d'
  on-tertiary-fixed: '#390c00'
  on-tertiary-fixed-variant: '#832600'
  background: '#faf8ff'
  on-background: '#191b24'
  surface-variant: '#e1e2ee'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 38px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.01em
  body-base:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  label-caps:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  code-log:
    fontFamily: Fira Sans
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  sidebar_width: 260px
  console_height: 200px
  gutter: 1.5rem
  container_padding: 2rem
  stack_gap_sm: 0.5rem
  stack_gap_md: 1rem
---

## Brand & Style
The design system is engineered for a high-performance video automation environment. It prioritizes clarity, technical precision, and user confidence. The aesthetic is **Corporate Modern**, leaning into a "Pro-Tool" feel that balances sophisticated utility with a clean, approachable interface. 

The target audience consists of developers and content creators who require a reliable, systematic workspace. The UI evokes a sense of "controlled power"—complex background processes are represented through a calm, organized, and high-contrast interface that minimizes cognitive load while maximizing throughput.

## Colors
The palette is anchored by "Tech Blue," signaling stability and innovation. The primary interaction color (#0066FF) is used for critical actions and active states. 

A specialized **Console Theme** is integrated specifically for log outputs and automation streams, utilizing a deep charcoal (#1E1E1E) to differentiate "system output" from "user configuration." Success states use a vibrant emerald to provide clear visual confirmation of task completion. Surface and background colors are intentionally low-saturation to keep the focus on content and data.

## Typography
The typographic system utilizes **Inter** for all UI elements to ensure maximum legibility at small sizes. The scale is tight and efficient, optimized for information-dense desktop applications. 

For technical logs and automation scripts, **Fira Sans** (serving as a highly legible humanist alternative to standard monospaces) is used to ensure that code characters are distinct and readable during rapid streaming. Use `label-caps` for section headers in sidebars and small metadata labels to create clear hierarchy without increasing font size.

## Layout & Spacing
The layout follows a **Fixed-Fluid-Fixed** vertical sandwich model:
1.  **Left Sidebar (Fixed):** 260px wide. Contains primary navigation and workspace switching.
2.  **Main Canvas (Fluid):** Expands to fill the remaining width. Content is organized in a 12-column grid or centered within a max-width container for better readability.
3.  **Bottom Console (Fixed Height):** 200px high, docked to the bottom. This acts as the persistent heartbeat of the automation tool.

Spacing follows an 8px base grid. Use `stack_gap_md` (16px) for the majority of component spacing to maintain a clean, professional "airy" feel within a technical tool.

## Elevation & Depth
This design system uses a **Tonal Layering** approach combined with low-contrast outlines.
- **Level 0 (Background):** #F8F9FA. The foundation.
- **Level 1 (Cards/Surface):** #FFFFFF. Used for main content modules. These feature a 1px solid border (#DEE2E6) and a very soft, diffused shadow (0px 2px 4px rgba(0,0,0,0.05)) to suggest subtle lift.
- **Level 2 (Popovers/Modals):** High-white with a more pronounced shadow (0px 8px 16px rgba(0,0,0,0.1)) to establish clear focus.

The console area uses a "sunken" effect—no shadow, but a darker background to indicate it is a separate functional plane.

## Shapes
A **Soft** shape language (4px - 8px radius) is employed to balance the technical nature of the app with modern UI trends. 
- **Standard Elements (Inputs, Buttons):** 4px (0.25rem) radius for a precise, "engineered" look.
- **Containers (Cards, Console):** 8px (0.5rem) radius to soften the larger layout blocks.
- **Segmented Controls:** Should mirror the input field radius for consistency.

## Components

### Buttons
- **Primary:** Solid #0066FF with white text. High-contrast, sharp 4px corners. On hover, darken to #0052CC.
- **Secondary:** #E3F2FD background with #0066FF text. No border.

### Input Fields
- White background with #DEE2E6 border. 
- Use 16px icons (Fluent UI style) for leading (context) or trailing (actions) positions. 
- Focus state: 1px #0066FF border with a 2px soft blue outer glow.

### Segmented Controls & Radios
- **Segmented Controls:** Use a "pill-within-a-track" look. Light gray background for the track, white elevated "chip" for the active state.
- **Radios:** Custom styled with a thick Tech Blue ring and white center dot when selected.

### Cards
- Use 1.5rem internal padding. 
- Header areas within cards should have a subtle bottom divider (#F1F3F5) to separate titles from configuration controls.

### Console Component
- Background: #1E1E1E. 
- Text: #D4D4D4 in Fira Sans.
- Success logs should be prepended with a #28A745 indicator. 
- The console should have a "clear" and "copy" action button anchored to the top-right corner, using low-opacity ghost styles.