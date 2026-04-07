# Contract: Analytics Page UI Sections

## Required Sections (2+ scans)

### 1. Key Metrics Delta Row
Horizontal row of cards showing change since last scan for:
- Body Weight (kg)
- Body Fat %
- Skeletal Muscle Mass (kg)
- BMI

Each card: metric name, current value, delta with ▲/▼ indicator and colour (green = improvement, red = decline).

### 2. Body Composition Summary Card
Plain-language card. Example outputs:
- "Your body fat percentage (18.2%) is in the Athletic range."
- "Your skeletal muscle mass is above average for your stats."
- "Muscle imbalance detected: right arm is 14% stronger than left arm."

### 3. Trend Charts
One chart per available metric from `data.history`. Grouped:
- Primary (always shown): body_weight_kg, body_fat_percentage, skeletal_muscle_mass_kg, BMI
- Secondary (shown if data present): fat_free_mass_kg, visceral_fat_level, basal_metabolic_rate_kcal, total_body_water_l

### 4. Muscle Balance Section
Only shown if segmental lean mass data available.
- Bar or comparison visual for: Left Arm vs Right Arm, Left Leg vs Right Leg
- Imbalance badge (>10% difference) with plain-language description

## Required Sections (1 scan)
- Body Composition Summary Card (current values only)
- Segmental snapshot bar chart
- Prompt: "Upload another scan to unlock progress tracking"

## Required Sections (0 scans)
- Empty state: "Upload your first InBody scan to see analytics"
- Call-to-action button linking to /scans
