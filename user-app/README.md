# HabitFlow × NudgeOps — User App Demo

A mobile-style habit tracker that demonstrates NudgeOps in action.
Shows the bandit learning in real time as users respond to nudges.

## What it shows

Left side — the "user app" (HabitFlow habit tracker):
- Pick any demo user from the dropdown
- Tap habits to mark them complete
- Hit "Get personalized nudge" to trigger the bandit
- React to the nudge (Done / Maybe / Skip / Ignore / Not helpful)

Right side — live NudgeOps bandit stats:
- All 10 arm success probabilities updating after each feedback
- Feedback log showing reward signal per interaction
- System-wide metrics (total nudges, completion rate, negative rate)

## How to run

1. Make sure the NudgeOps backend is running:
   ```
   cd backend
   uvicorn main:app --reload --port 8000
   ```

2. Open the user app — just double-click `user-app/index.html` in your browser.
   No server needed. It's a single HTML file.

## No training needed

The bandit learns live from feedback. First nudge uses equal priors.
By the 5th–10th interaction the arm bars will visibly shift toward
whatever strategy the selected user responds to best.

## What the feedback buttons do

| Button    | Signal    | Reward  | Bandit update        |
|-----------|-----------|---------|----------------------|
| Done it!  | completed | +1.0    | α increases strongly |
| Maybe     | engaged   | +0.5    | α increases slightly |
| Skip      | dismissed | −0.2    | β increases          |
| Ignore    | ignored   |  0.0    | No change            |
| Not helpful | negative | −0.5  | β increases strongly |

The arm bars reflect α/(α+β) — the Beta distribution mean —
which is the bandit's current estimate of how likely each
strategy is to get a positive response from this specific user.
