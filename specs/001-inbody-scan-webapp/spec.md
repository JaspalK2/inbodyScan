# Feature Specification: InBody Scan Health Web Application

**Feature Branch**: `001-inbody-scan-webapp`  
**Created**: 2026-03-30  
**Status**: Draft  
**Input**: User description: "As a user I want to build a web application that is capable of interpretting in-body scans, and recommending the user diet / workout plans based off their goals (these should be selected by the user). In this web app there should be a dashboard showing their current progress from their current scan and their pervious scan. There should be a way to see all their metrics displayed via graphs of differnt types that illustrate readings from the inbody scans. This can be in the form of fat percatage, muscle mass, etc. There should be a login page (username and password). There should be an admin portal, so that this account could add additional users. Every individual user should only be able to view their own data and no one else's. Reccomendations for food and workouts should be made with the cheapest LLM models. There must be an User profile, a location for inputting their age, height etc (some of which could be given via the inbody scan pdf). Any predictions for food should take into account the users dietary restrictios if any i.e if a user does not eat meat / eggs/ has allergies of any sort. The diet reccomendation system should display all form of macros, calories, fat, vitamins, protien, and should be backed up by actual health datasets (should be real). For now we will build just this, and add more items later on."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Secure Login and Account Access (Priority: P1)

A user visits the web application and is presented with a login screen. They enter their username and password to access their personal health dashboard. Users who are not logged in cannot access any part of the application. Each user is strictly isolated — they can only view and interact with their own data.

**Why this priority**: Authentication and data isolation are foundational. Without these, no other feature can be safely deployed.

**Independent Test**: Can be fully tested by creating two user accounts, logging in as each, and verifying that neither account can access the other's data. Delivers the value of a secure, private health data portal.

**Acceptance Scenarios**:

1. **Given** a registered user exists, **When** they enter a valid username and password, **Then** they are granted access to their personal dashboard and no other user's data.
2. **Given** an unauthenticated visitor, **When** they attempt to access any protected page, **Then** they are redirected to the login page.
3. **Given** a logged-in user, **When** they attempt to access another user's data via URL manipulation, **Then** they receive an access-denied response and are not shown any other user's data.
4. **Given** a user with incorrect credentials, **When** they attempt to log in, **Then** they receive a clear error message and are not granted access.

---

### User Story 2 - InBody Scan Upload and Data Extraction (Priority: P1)

A registered user uploads their InBody scan as a PDF. The system reads and extracts health metrics from the PDF — such as body fat percentage, muscle mass, visceral fat level, body water, BMI, and segmental analysis — and stores them against the user's profile. This becomes the data source for all dashboard views, graphs, and recommendations.

**Why this priority**: All other features (dashboard, graphs, recommendations) depend on successfully parsed scan data. Without scan data, there is nothing to display or act on.

**Independent Test**: Can be fully tested by uploading a sample InBody PDF and confirming that extracted values match the PDF contents. Delivers the value of a digitized health record.

**Acceptance Scenarios**:

1. **Given** a logged-in user, **When** they upload a valid InBody scan PDF, **Then** the system extracts all available metrics (body fat %, muscle mass, BMI, body water, visceral fat, etc.) and saves them with the scan date.
2. **Given** a user with multiple uploaded scans, **When** they view their data, **Then** each scan is stored separately with its corresponding date so historical comparisons are possible.
3. **Given** a user uploads an unrecognized or corrupt PDF, **When** extraction is attempted, **Then** the user receives a clear error message explaining the issue and no partial data is saved.
4. **Given** a scan PDF that contains data also present in the user's profile (e.g., height, weight), **When** the scan is uploaded, **Then** the system pre-populates matching profile fields if they are not already filled in.

---

### User Story 3 - Progress Dashboard (Priority: P2)

A logged-in user views their main dashboard, which presents a side-by-side or comparative view of their most recent scan and their previous scan. Key body composition metrics are highlighted with indicators showing improvement, decline, or no change. The dashboard gives the user an at-a-glance understanding of how their body has changed between the two most recent scans.

**Why this priority**: The dashboard is the central experience of the app and the primary reason users return after each new scan.

**Independent Test**: Can be fully tested with two uploaded scans for a single user; dashboard must correctly display both and calculate change values for each metric.

**Acceptance Scenarios**:

1. **Given** a user with two or more scans, **When** they view the dashboard, **Then** their most recent and second-most-recent scans are displayed side-by-side with delta indicators (e.g., +1.2 kg muscle, -0.8% body fat).
2. **Given** a user with only one scan, **When** they view the dashboard, **Then** they see their single scan's metrics clearly, with a prompt to upload a second scan to unlock comparison.
3. **Given** a user with no scans uploaded, **When** they view the dashboard, **Then** they see an empty state with a clear call-to-action to upload their first scan.
4. **Given** a user's scan data, **When** displayed on the dashboard, **Then** all metric changes include a visual indicator (e.g., up arrow, down arrow, neutral) so the user can interpret trends at a glance.

---

### User Story 4 - Metrics Visualization via Graphs (Priority: P2)

A user navigates to a dedicated metrics section where their historical scan data is displayed through multiple chart types. Different metrics are visualized in the most appropriate chart format — for example, body fat percentage and muscle mass trends over time via line charts, body composition breakdown via pie or donut charts, and segmental analysis via bar charts. Users can see their full health history graphically.

**Why this priority**: Graphs transform raw numbers into meaningful trends, increasing user engagement and health literacy.

**Independent Test**: Can be tested with at least three uploaded scans; all major metrics must render correctly in their respective chart types.

**Acceptance Scenarios**:

1. **Given** a user with multiple scans, **When** they view the metrics page, **Then** at least three distinct chart types are present, each showing a different aspect of their body composition over time.
2. **Given** a metric with data points across multiple scans, **When** displayed as a trend chart, **Then** dates are shown on the x-axis and metric values on the y-axis with clear labeling.
3. **Given** a user with a single scan, **When** they view the metrics page, **Then** charts that require multiple data points show a placeholder message, while single-scan charts (e.g., body composition breakdown) display correctly.
4. **Given** any chart, **When** the user hovers over or taps a data point, **Then** the exact value and date are displayed in a tooltip.

---

### User Story 5 - User Profile and Health Information (Priority: P2)

A user can view and edit their profile, including personal details such as age, biological sex, height, and health-relevant information. Some fields may be auto-populated from their most recent InBody scan PDF. The profile also includes dietary restrictions and allergies (e.g., vegetarian, vegan, no eggs, nut allergy), which directly influence diet recommendations. Users also select their health goal(s) from a predefined list (e.g., fat loss, muscle gain, maintain weight, improve endurance).

**Why this priority**: Profile data, dietary restrictions, and goals are prerequisites for generating personalized and safe recommendations.

**Independent Test**: Can be fully tested by completing a profile, setting a dietary restriction, selecting a goal, and verifying that the saved data persists correctly across sessions.

**Acceptance Scenarios**:

1. **Given** a logged-in user, **When** they access their profile, **Then** they can view and edit: age, biological sex, height, weight (if not from scan), dietary restrictions, allergies, and health goals.
2. **Given** a user who uploads an InBody scan containing height or weight data, **When** the scan is processed, **Then** those values are pre-filled in their profile if the fields are currently empty.
3. **Given** a user who selects dietary restrictions (e.g., vegetarian, no nuts), **When** diet recommendations are generated, **Then** no recommendations include restricted food items.
4. **Given** a user who selects a health goal (e.g., "Lose body fat"), **When** recommendations are generated, **Then** all recommendations are contextualized toward that goal.
5. **Given** a user with no goal selected, **When** they attempt to generate recommendations, **Then** they are prompted to select a goal before proceeding.

---

### User Story 6 - AI-Powered Diet Recommendations (Priority: P2)

Based on the user's latest scan data, profile, dietary restrictions, and selected health goal, the system generates a personalized diet recommendation. The recommendation includes a full nutritional breakdown: daily calorie target, macronutrients (protein, carbohydrates, fat), micronutrients (key vitamins and minerals), and suggested meal ideas. Nutritional values are grounded in real health datasets (e.g., USDA FoodData Central or equivalent). The system uses a cost-efficient AI model to generate recommendations.

**Why this priority**: Diet recommendations are a core differentiator and primary value proposition of the app.

**Independent Test**: Can be tested by generating a recommendation for a user with a complete profile and scan, then verifying the output includes all required nutritional categories and respects dietary restrictions.

**Acceptance Scenarios**:

1. **Given** a user with a complete profile, at least one scan, dietary restrictions set, and a goal selected, **When** they request a diet recommendation, **Then** the system returns a structured plan including daily calorie target, protein, carbohydrates, fat, and key vitamins and minerals.
2. **Given** a user who has selected "vegetarian" as a dietary restriction, **When** a diet recommendation is generated, **Then** no meat or fish appears in any suggested meals.
3. **Given** a user with a nut allergy, **When** a diet recommendation is generated, **Then** nuts and nut-derived ingredients are excluded from all suggestions.
4. **Given** a diet recommendation, **When** displayed to the user, **Then** each macro and micronutrient is shown with its recommended daily amount and the percentage of the daily target it represents.
5. **Given** nutritional values in the recommendation, **When** any specific food item is referenced, **Then** its nutritional data is consistent with established health datasets such as USDA FoodData Central.

---

### User Story 7 - AI-Powered Workout Recommendations (Priority: P3)

Based on the user's latest scan data, profile details, and selected health goal, the system generates a personalized workout plan. The plan includes exercise types, frequency, duration, and intensity guidance aligned to the user's goal (e.g., resistance training for muscle gain, cardio-focused for fat loss). The system uses a cost-efficient AI model to generate these recommendations.

**Why this priority**: Workout recommendations complement diet recommendations and complete the health guidance loop, but the app delivers standalone value without them.

**Independent Test**: Can be tested by generating a workout recommendation for a user with a complete profile and scan, verifying the output includes exercise types, weekly frequency, and duration guidance aligned to the user's goal.

**Acceptance Scenarios**:

1. **Given** a user with a complete profile, at least one scan, and a health goal selected, **When** they request a workout recommendation, **Then** the system returns a structured weekly workout plan with exercise types, frequency, and duration.
2. **Given** a user whose goal is "Lose body fat", **When** a workout recommendation is generated, **Then** the plan emphasizes cardiovascular and calorie-burning activities.
3. **Given** a user whose goal is "Gain muscle mass", **When** a workout recommendation is generated, **Then** the plan emphasizes resistance and strength training.
4. **Given** a workout recommendation, **When** displayed, **Then** each exercise or session block includes a description sufficient for the user to understand what to do.

---

### User Story 8 - Admin Portal: User Management (Priority: P3)

An administrator logs in with admin credentials and accesses a dedicated admin portal. From the portal, the admin can create new user accounts by setting a username and temporary password. The admin can view a list of all registered users (names and account status only — not health data). The admin cannot view individual users' health data, scan results, or recommendations.

**Why this priority**: The admin portal enables controlled onboarding of users, which is required for a closed-access deployment.

**Independent Test**: Can be fully tested by logging in as an admin, creating a new user account, and verifying the new user can log in and that the admin cannot access the new user's health data.

**Acceptance Scenarios**:

1. **Given** an admin account, **When** the admin logs in, **Then** they are directed to the admin portal, not the regular user dashboard.
2. **Given** the admin portal, **When** an admin creates a new user with a username and temporary password, **Then** the new user account is created and the user can log in with those credentials.
3. **Given** the admin portal, **When** an admin views the user list, **Then** they see only usernames and account status — no health metrics, scans, or recommendations are visible.
4. **Given** an admin account, **When** the admin attempts to access a user's health data or scan records, **Then** they receive an access-denied response.
5. **Given** a regular user account, **When** the user attempts to access the admin portal URL, **Then** they receive an access-denied response.

---

### Edge Cases

- What happens when an uploaded PDF is a valid PDF but not an InBody scan format?
- What happens if a scan PDF is missing certain expected fields (e.g., no segmental analysis data)?
- How does the system handle a user who changes their dietary restriction after a recommendation has already been generated?
- What happens if the AI model is unavailable when a user requests a recommendation? → **Resolved**: The request is queued. The user sees a "generating…" status indicator. The page auto-refreshes or notifies the user when the recommendation is ready, up to a maximum 5-minute wait. If still unresolved after 5 minutes, the user is shown an error with the option to retry.
- What happens when a user uploads a scan with the same date as an existing scan (duplicate upload)? → **Resolved**: The upload is rejected with a clear error message: "A scan for this date already exists. Delete the existing scan first if you want to replace it." No data is overwritten silently.
- How does the system handle metric values that fall outside typical human ranges?
- What if a user's health goal conflicts with their scan data in a clinically significant way (e.g., a severely underweight user selecting "Lose body fat")? → **Resolved**: The system allows the goal selection but displays a prominent one-time warning informing the user that their current metrics may not support this goal and recommending they consult a health professional before proceeding.

---

## Requirements *(mandatory)*

### Functional Requirements

**Authentication and Access Control**

- **FR-001**: The system MUST require a valid username and password to access any protected page or feature.
- **FR-002**: The system MUST prevent any user from viewing, modifying, or inferring another user's data, including scans, profile information, and recommendations.
- **FR-003**: The system MUST maintain separate access levels for regular users and administrators.
- **FR-004**: The system MUST redirect unauthenticated users to the login page when they attempt to access protected routes.

**Scan Upload and Data Extraction**

- **FR-005**: The system MUST accept InBody scan files in PDF format.
- **FR-006**: The system MUST extract and store all available body composition metrics from the uploaded scan, including but not limited to: body fat percentage, skeletal muscle mass, body mass index, total body water, visceral fat level, and segmental muscle and fat analysis.
- **FR-007**: The system MUST associate each scan with the date it was recorded (from the PDF, falling back to the upload date) and the user who uploaded it.
- **FR-007a**: The system MUST enforce a uniqueness constraint of one scan per user per scan date. If a user uploads a PDF whose resolved scan date matches an existing scan, the upload MUST be rejected with the message: "A scan for this date already exists. Delete the existing scan first if you want to replace it."
- **FR-008**: The system MUST display a clear error message when a PDF cannot be parsed or does not contain recognizable InBody data.
- **FR-009**: The system MUST auto-populate compatible user profile fields (e.g., height, weight) from scan data when those fields are currently empty.

**Dashboard**

- **FR-010**: The system MUST display a comparison of the user's two most recent scans on the dashboard, including delta values for each metric.
- **FR-011**: The system MUST provide visual indicators (e.g., directional arrows or color coding) to show whether each metric has improved, declined, or remained stable relative to the user's goal.
- **FR-012**: The system MUST show an empty state with upload guidance when the user has no scans on file.

**Metrics and Graphs**

- **FR-013**: The system MUST display historical scan data in graphical form using at least three distinct chart types appropriate to the data being shown (e.g., line chart for trends, pie or donut chart for composition breakdown, bar chart for segmental analysis).
- **FR-014**: The system MUST label all chart axes, legends, and data points clearly.
- **FR-015**: The system MUST display exact metric values and scan dates when a user interacts with a data point on a chart.

**User Profile**

- **FR-016**: The system MUST allow users to set and update their age, biological sex, height, and health goal(s).
- **FR-017**: The system MUST allow users to specify dietary restrictions from a predefined list including at minimum: vegetarian, vegan, no eggs, no dairy, no gluten.
- **FR-018**: The system MUST allow users to add free-text allergy entries in addition to predefined restrictions.
- **FR-019**: The system MUST require at least one health goal to be selected before generating any recommendations.
- **FR-019a**: When a user selects a health goal that is clinically inconsistent with their most recent scan data (e.g., a BMI below 18.5 paired with a "Lose body fat" goal), the system MUST display a prominent one-time warning advising the user that their current metrics may not support this goal and recommending consultation with a health professional. The user MUST be able to acknowledge and proceed — the system MUST NOT block the goal selection.

**Diet Recommendations**

- **FR-020**: The system MUST generate personalized diet recommendations using a cost-efficient AI language model, informed by the user's scan data, profile, dietary restrictions, and health goal.
- **FR-020a**: Every generated diet recommendation MUST be stored and retained in full. The system MUST provide a recommendation history view where the user can browse all past diet recommendations, ordered by generation date descending.
- **FR-021**: Diet recommendations MUST include: daily calorie target, macronutrient targets (protein, carbohydrates, total fat), and key micronutrient guidance (including at minimum vitamins D, B12, and C, plus iron, calcium, and potassium).
- **FR-022**: Diet recommendations MUST NOT include any food or ingredient that conflicts with the user's specified dietary restrictions or allergies.
- **FR-023**: Nutritional values presented in recommendations MUST be consistent with data from an established human nutrition dataset (e.g., USDA FoodData Central).
- **FR-024**: Diet recommendations MUST display each nutrient with its recommended daily target amount and the percentage it contributes toward that target.

**Workout Recommendations**

- **FR-025**: The system MUST generate personalized workout recommendations using a cost-efficient AI language model, informed by the user's scan data, profile, and health goal.
- **FR-025b**: Every generated workout recommendation MUST be stored and retained in full. The system MUST provide a recommendation history view where the user can browse all past workout recommendations, ordered by generation date descending.
- **FR-025a**: Recommendation requests (diet and workout) MUST be queued asynchronously. The user MUST be shown a "generating…" status that auto-updates when the result is ready. If a result is not available within 5 minutes, the system MUST display an error and offer a one-click retry option.
- **FR-026**: Workout recommendations MUST include exercise types, weekly frequency, session duration, and basic intensity guidance.
- **FR-027**: Workout recommendations MUST be aligned to the user's stated health goal.

**Admin Portal**

- **FR-028**: The system MUST provide a separate admin portal accessible only to accounts with administrator privileges.
- **FR-029**: Administrators MUST be able to create new user accounts by specifying a username and initial password.
- **FR-030**: Administrators MUST be able to view a list of all registered user accounts showing only username and account status.
- **FR-031**: Administrators MUST NOT be able to access any individual user's health data, scans, profile details, or recommendations.

---

### Key Entities

- **User**: A registered individual with a username, password, role (user or admin), and profile data. Each user has a strictly isolated data space.
- **Admin**: A privileged user type with access only to account management features, not health data.
- **UserProfile**: Stores age, biological sex, height, weight (if not from scan), dietary restrictions, allergens, and health goals, linked to a User.
- **InBodyScan**: A single scan record associated with a User, containing a scan date and all extracted body composition metrics.
- **ScanMetric**: A specific measured value (e.g., body fat %, skeletal muscle mass) from a given InBodyScan.
- **HealthGoal**: A user-selected objective (e.g., Lose Body Fat, Gain Muscle Mass, Maintain Weight, Improve Endurance) that drives recommendation generation.
- **DietaryRestriction**: A user-specified food restriction or allergy (predefined or free-text) that constrains diet recommendations.
- **DietRecommendation**: A generated dietary plan for a User at a point in time, including calorie targets, macros, key micronutrients, and meal suggestions.
- **WorkoutRecommendation**: A generated exercise plan for a User at a point in time, including exercise types, frequency, and duration.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can log in and reach their dashboard within 10 seconds of submitting valid credentials under normal conditions.
- **SC-002**: InBody scan PDF upload and data extraction completes within 30 seconds for a standard single-page InBody report.
- **SC-003**: The dashboard accurately reflects delta values for all extracted metrics between the two most recent scans with zero calculation errors.
- **SC-004**: Diet and workout recommendations are generated and displayed to the user within 60 seconds of request submission.
- **SC-005**: 100% of generated diet recommendations exclude all food items conflicting with the user's stated dietary restrictions and allergies, with zero violations across tested scenarios.
- **SC-006**: Nutritional values in diet recommendations match established nutrition dataset values within a 5% margin on spot-check validation.
- **SC-007**: No user can access another user's data under any tested access scenario, achieving zero data isolation breaches.
- **SC-008**: Admin users can create a new user account and the account becomes functional for login within 60 seconds of creation.
- **SC-009**: At least 90% of expected metric fields from a standard InBody scan PDF are successfully extracted with correct values.
- **SC-010**: All chart types on the metrics page render correctly and completely for users with three or more scan records.

---

## Clarifications

### Session 2026-03-31

- Q: What happens if the AI model is unavailable when a user requests a recommendation? → A: Queue the request; user sees "generating…" status and the page auto-updates when ready (up to 5 min wait).
- Q: When a user generates a new recommendation, does it replace the previous one or accumulate as a browsable history? → A: Keep history — every generated recommendation is retained and the user can browse past recommendations.
- Q: What happens if a user's health goal conflicts with their scan data in a clinically significant way (e.g., severely underweight selecting "Lose body fat")? → A: Allow the goal but display a prominent one-time warning that scan data may not support the goal and recommend consulting a professional.
- Q: What happens when a user uploads a scan with the same date as an existing scan? → A: Reject with a clear error: "A scan for this date already exists. Delete the existing scan first if you want to replace it."

## Assumptions

- Users will upload standard InBody scan PDF reports as produced by InBody brand devices. Non-InBody PDF formats and handwritten records are out of scope for v1.
- The application is a web-based product accessed via a modern desktop or mobile web browser. A native mobile app is out of scope for v1.
- All users are invited by an administrator — there is no self-registration. Only admins can create new user accounts.
- The application handles sensitive personal health data and must be treated accordingly. Secure data transmission and encrypted storage at rest are assumed as baseline requirements.
- "Cheapest LLM model" is interpreted as using the lowest-cost commercially available AI model tier that produces coherent, structured health guidance. The specific provider will be determined during planning.
- Nutritional data backing diet recommendations will be sourced from the USDA FoodData Central database (publicly available and free to use), unless a superior equivalent is identified during planning.
- Dietary restrictions and allergens are self-reported by the user. The system is not a medical device and does not provide clinical dietary advice. A standard health disclaimer will be shown alongside recommendations.
- Workout recommendations do not require dataset backing in v1 and are generated by the AI model based on the user's profile and scan data. A medical disclaimer will be included.
- An "admin" is a single privileged role type. There is no hierarchy of admins or sub-admin roles in v1.
- The initial deployment serves a small user base (under 500 users). High-availability infrastructure and horizontal scaling are not requirements for v1.
- Health goals are selected from a predefined list. Custom free-text goal entry is out of scope for v1.
- Mobile responsiveness is desirable but full mobile-first optimization is a v2 consideration. The app must remain functional and non-broken on mobile viewports.
