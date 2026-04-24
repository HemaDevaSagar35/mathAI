# F08 — Progress Dashboard

> **Objective:** Show the user's learning progress: streak, book progress, weak/strong concepts, quiz averages, and recent activity.

**Depends on:** F01 (skeleton), Backend B13 (progression/mastery endpoints)

---

## Tasks

### 1. API functions — `src/api/progress.ts`

```typescript
export async function getProgress(): Promise<ProgressDashboard> {
  const res = await apiClient.get("/progress");
  return res.data;
}

export async function getConceptMastery(): Promise<ConceptMastery[]> {
  const res = await apiClient.get("/progress/concepts");
  return res.data;
}
```

### 2. Progress screen — `app/progress.tsx`

```text
┌──────────────────────────────┐
│  🔥 4-day streak             │
│                              │
│  Active Book                 │
│  ┌────────────────────────┐  │
│  │ Linear Algebra Ch. 2   │  │
│  │ Progress: 32%          │  │
│  │ ═══════░░░░░░░░░░░░░░  │  │
│  │ Current: Span          │  │
│  │ Next: Linear Indep.    │  │
│  └────────────────────────┘  │
│                              │
│  Quiz Performance            │
│  Average: 74%                │
│  Last 5: 80 72 65 90 68     │
│                              │
│  Concept Mastery             │
│  ┌────────────────────────┐  │
│  │ ● Vector         92%   │  │  green
│  │ ● Scalar Mult.   85%   │  │  green
│  │ ● Lin. Combo     71%   │  │  yellow
│  │ ○ Span           45%   │  │  orange (weak)
│  │ ○ Basis          30%   │  │  red (weak)
│  └────────────────────────┘  │
│                              │
│  Recent Activity             │
│  ┌────────────────────────┐  │
│  │ Today  Completed T3    │  │
│  │ Today  Quiz: 72%       │  │
│  │ Yest.  Completed T2    │  │
│  │ Yest.  Quiz: 85%       │  │
│  └────────────────────────┘  │
└──────────────────────────────┘
```

### 3. Streak display component

Show flame icon + count. Animate on current-day completion.

### 4. Concept mastery bars

Horizontal bars colored by mastery level:
- >= 0.8 → green
- 0.6–0.8 → yellow
- 0.4–0.6 → orange
- < 0.4 → red

Sorted by mastery score (weakest first, or strongest first with toggle).

### 5. Recent activity list

Show last 10 events with:
- Date
- Event type (lesson completed, quiz taken, question asked)
- Score if applicable

### 6. Hook

```typescript
export function useProgress() {
  return useQuery({ queryKey: ["progress"], queryFn: getProgress });
}
```

---

## Files to Create/Modify

```text
src/api/progress.ts
app/progress.tsx              (replace placeholder)
```

---

## Acceptance Criteria

- [ ] Dashboard shows current streak count.
- [ ] Active book section shows title, progress bar, current tidbit.
- [ ] Quiz performance shows average and recent scores.
- [ ] Concept mastery section lists all concepts with color-coded bars.
- [ ] Weak concepts (mastery < 0.5) are highlighted.
- [ ] Recent activity shows last 10 events.
- [ ] Screen loads data from backend and handles loading/error states.

---

## Agent Prompt

```text
Build progress dashboard for MathPath:

1. src/api/progress.ts — getProgress, getConceptMastery.
2. app/progress.tsx — dashboard with: streak count, active book progress, quiz performance average, concept mastery bars (color-coded by level), recent activity list.
3. Color mastery bars: green >=0.8, yellow 0.6-0.8, orange 0.4-0.6, red <0.4.
4. Show weak concepts prominently. Sort by mastery score.
5. Handle loading and error states gracefully.
```
