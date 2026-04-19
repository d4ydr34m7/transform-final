# VERAMOD UI Specification - Complete Prompt

Build a pure React + TypeScript UI for an internal enterprise tool called VERAMOD.
This is UI only with mocked data.
Follow the layout, styling, and wording exactly as specified.
Do not redesign or add extras.

## Tech Constraints (STRICT)

- React + TypeScript
- No external UI libraries (no MUI, Chakra, Ant, Tailwind, etc.)
- Plain CSS or CSS Modules only
- No icons (except for dropdown arrow using SVG data URI)
- No animations (only simple hover transitions)
- No gradients (except for logo), no glassmorphism
- Enterprise internal tool look only

## Global Theme (LOCKED)

### Colors
- Navbar background: deep navy `#0b1f3a`
- Page background: off-white `#f4f6fb`
- Primary action blue: `#2563eb`
- Hover / confirm: subtle enterprise green `#4ade80` (not neon)
- Text: dark slate / charcoal (not pure black)
- Border colors: `#e5e7eb`, `#d1d5db`
- Subtle backgrounds: `#f9fafb`, `#fafbfc`

### Typography
- **Font Family**: Source Sans Pro (primary), with system font fallbacks
- Use Source Sans Pro from Google Fonts
- Headings: slightly heavier weights (600-700)
- Body text: calm, readable (400-500)
- Letter spacing: 0.01em for body, -0.02em for large headings
- No playful or consumer styling

## SHARED NAVBAR (ALL PAGES)

### Layout
- Full-width top navbar
- Background: `#0b1f3a`
- Very subtle shadow for depth: `box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1)`
- Padding: `1.5rem 2rem`

### Navbar Content (Horizontal Layout)
- **Logo Icon** (left side):
  - Abstract transform-themed logo
  - 40x40px size
  - CSS-based geometric design using gradients
  - Rotated square with inner elements suggesting transformation
  - Gradient: `linear-gradient(135deg, #2563eb 0%, #4ade80 100%)`
  - Rounded corners: `border-radius: 6px`
  
- **Brand Text** (inline, to the right of logo):
  - Container with flex layout, gap: `0.75rem`
  - **VERAMOD**:
    - Font: Source Sans Pro
    - Size: `1.75rem`
    - Weight: `700`
    - Color: `#f4f6fb` (soft off-white)
    - Letter spacing: `-0.02em`
  - **let's analyze !** (inline, same line):
    - Font: Source Sans Pro
    - Size: `0.875rem`
    - Weight: `400`
    - Color: `#9ca3af` (greyish/muted)
    - Not bold, not capitalized
    - Calm, understated

Navbar must feel serious, internal, and trustworthy.

## PAGE 1 — Repo Selection / Analyze

### Layout
- Off-white page background: `#f4f6fb`
- Centered content (vertically and horizontally)
- One main repo selection card

### Repo Selection Card
- **Card Style**:
  - Enterprise-grade card
  - Subtle rounded corners: `border-radius: 8px`
  - Light border: `1px solid #e5e7eb`
  - Soft shadow: `box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05)`
  - White background: `#ffffff`
  - Padding: `2.5rem 3rem`
  - Max width: `500px`
  - Card must feel clean, confident, and calm
  - No unnecessary decoration

- **Label**: "Select Repository"
  - Font: Source Sans Pro
  - Size: `0.875rem`
  - Weight: `600`
  - Color: `#374151`
  - Letter spacing: `0.01em`
  - Margin bottom: `0.75rem`

- **Input Row** (horizontal layout):
  - Flex container with gap: `1rem`
  - **Dropdown** (flex: 1):
    - Native select element styled
    - Padding: `0.75rem 1rem`
    - Border: `1px solid #d1d5db`
    - Border radius: `4px`
    - Font: Source Sans Pro, `1rem`
    - Custom dropdown arrow using SVG data URI
    - Placeholder option: "Select a repository..."
    - Mock repos: `['org/repo-name', 'acme/backend-service', 'acme/frontend-app', 'acme/data-pipeline', 'acme/api-gateway']`
  
  - **Primary Button**: "Run Analysis" (right side)
    - Padding: `0.75rem 1.5rem`
    - Default color: `#2563eb`
    - Hover / Active: `#4ade80` (subtle green)
    - Font: Source Sans Pro, `1rem`, weight `600`
    - White text
    - Border radius: `4px`
    - White space: nowrap
    - Letter spacing: `0.01em`

### Behavior (Mocked)
- Clicking "Run Analysis" navigates to Page 2 (`/analysis` route)

## PAGE 2 — Analysis Results

### Layout
- Same navbar as Page 1
- Off-white page background: `#f4f6fb`
- Full-height layout

### Top Row
- **Left-aligned text**: "Analysis artifacts are ready"
  - Font: Source Sans Pro, `1rem`, weight `500`
  - Color: `#374151`
  - Letter spacing: `0.01em`
  
- **Right-aligned button**: "Download Analysis"
  - Subtle, enterprise-style button
  - Padding: `0.625rem 1.25rem`
  - Background: `#2563eb`
  - Hover: `#4ade80`
  - Font: Source Sans Pro, `0.875rem`, weight `600`
  - Letter spacing: `0.01em`

### Main Workspace — 3-Pane Layout (FULL HEIGHT)

Split horizontally into three fixed panes. Full height below top row.

#### LEFT PANE — File Explorer
- **Width**: `280px` (fixed)
- **Background**: Slightly tinted off-white `#f9fafb`
- **Title**: "ANALYSIS FILES"
  - Font: Source Sans Pro, `0.75rem`, weight `700`
  - Uppercase
  - Letter spacing: `0.08em`
  - Color: `#6b7280`
  - Padding: `1rem 1.25rem`
  - Border bottom: `1px solid #e5e7eb`
  
- **Mock File Tree**:
  - Plain text list (no icons)
  - Scrollable area
  - Files:
    ```
    /analysis
    architecture.md
    risks.md
    dependencies.json
    modernization-notes.md
    ```
  - Font: Source Sans Pro, `0.875rem`
  - Color: `#374151`
  - Padding: `0.5rem 1.25rem` per item
  - Cursor: pointer
  - Selected file: subtle highlight
    - Background: `#e0e7ff`
    - Color: `#1e40af`
  - Hover: `#f3f4f6`

#### CENTER PANE — Document Viewer
- **Flex**: 1 (takes remaining space)
- **Background**: White `#ffffff`
- **Title**: "DOCUMENT VIEWER"
  - Same styling as left pane title
  
- **Content Area**:
  - Background: `#fafbfc` (subtle tint)
  - Padding: `3rem`
  - Scrollable
  
- **Empty State**:
  - Centered text: "Select a file to view analysis."
  - Font: Source Sans Pro, `1rem`, weight `400`
  - Color: `#9ca3af`
  - Letter spacing: `0.01em`
  
- **When File Selected**:
  - **Document Container**:
    - Max width: `900px`
    - Centered
    - White background: `#ffffff`
    - Border: `1px solid #e5e7eb`
    - Border radius: `8px`
    - Box shadow: `0 2px 8px rgba(0, 0, 0, 0.06)`
    - Padding: `3rem`
    - Pops up with elevated appearance
  
  - **Markdown Content Rendering**:
    - Parse and render markdown-style content
    - Font: Source Sans Pro, `1rem`
    - Line height: `1.75`
    - Color: `#111827`
    - Letter spacing: `0.01em`
    
    - **Headings**:
      - H1: `2rem`, weight `700`, color `#111827`, letter spacing `-0.02em`, line height `1.3`
      - H2: `1.5rem`, weight `600`, color `#1f2937`, letter spacing `-0.01em`, line height `1.4`
      - H3: `1.25rem`, weight `600`, color `#374151`, line height `1.4`
    
    - **Paragraphs**: Margin `1rem 0`, line height `1.75`
    
    - **Lists**:
      - Margin: `1.25rem 0`
      - Padding left: `2rem`
      - List items: margin `0.5rem 0`, line height `1.6`
    
    - **Code**:
      - Inline: background `#f3f4f6`, padding `0.125rem 0.375rem`, border radius `3px`, font size `0.9em`, weight `500`
      - Code blocks: background `#f9fafb`, border `1px solid #e5e7eb`, border radius `6px`, padding `1.5rem`, font size `0.9rem`
    
    - **Strong/Bold**: Weight `600`, color `#1f2937`
    
    - Comfortable reading width
    - Generous padding

#### RIGHT PANE — Chat
- **Width**: `320px` (fixed)
- **Background**: White `#ffffff`
- **Title**: "ASK QUESTIONS"
  - Same styling as other pane titles
  
- **Content Area**:
  - Flex column layout
  - Full height
  
- **Empty State**:
  - Text: "No messages yet. Ask a question to get started."
  - Font: Source Sans Pro, `0.875rem`, weight `400`
  - Color: `#9ca3af`
  - Centered, padding `2rem`
  - Letter spacing: `0.01em`
  
- **Bottom Input Box**:
  - Container: flex row, gap `0.5rem`, padding `1rem`
  - Border top: `1px solid #e5e7eb`
  - **Input Field**:
    - Placeholder: "Ask a question about the analysis..."
    - Flex: 1
    - Padding: `0.625rem 0.875rem`
    - Border: `1px solid #d1d5db`
    - Border radius: `4px`
    - Font: Source Sans Pro, `0.875rem`, weight `400`
    - Letter spacing: `0.01em`
  
  - **Submit Button**:
    - Text: "Submit"
    - Background: `#2563eb` (blue)
    - Hover: `#4ade80`
    - Padding: `0.625rem 1.25rem`
    - Font: Source Sans Pro, `0.875rem`, weight `600`
    - Letter spacing: `0.01em`
  
- **Content Display**:
  - Simple Q&A list
  - No avatars
  - No chat bubbles
  - **Questions**: Font Source Sans Pro, `0.875rem`, weight `600`, color `#374151`, letter spacing `0.01em`
  - **Answers**: Font Source Sans Pro, `0.875rem`, weight `400`, color `#6b7280`, line height `1.6`, letter spacing `0.01em`
  - Message spacing: `1.5rem` between messages
  - Enterprise, restrained look

### Behavior (Mocked)
- File selection updates document viewer
- Chat questions/answers are mocked
- Enter key submits chat question

## Mocked Data

### Repositories (Page 1)
- `org/repo-name`
- `acme/backend-service`
- `acme/frontend-app`
- `acme/data-pipeline`
- `acme/api-gateway`

### Analysis Files (Page 2)
- `/analysis` (folder, not selectable)
- `architecture.md`
- `risks.md`
- `dependencies.json`
- `modernization-notes.md`

### Document Content (Mocked Markdown)
Each file contains markdown-formatted content that should be parsed and rendered with proper styling (headers, lists, code blocks, bold text).

## Implementation Notes

1. Use React Router for navigation between pages
2. Implement markdown parsing function for document viewer
3. All fonts must be Source Sans Pro with proper fallbacks
4. Ensure proper letter spacing throughout
5. Document viewer should have elevated card appearance when content is displayed
6. All hover states use the green color `#4ade80`
7. Maintain consistent spacing and padding throughout
8. No external dependencies except React, React Router, and TypeScript
