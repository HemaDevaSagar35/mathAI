# F03 — Book Profile & Study Plan UI

> **Objective:** Show the detected book profile and render the stable tidbit roadmap with status indicators.

**Depends on:** F01 (skeleton), F02 (books), Backend B05 (profile), B08 (plan)

---

## Tasks

### 1. API functions — `src/api/books.ts` (extend)

```typescript
export async function getStudyPlan(bookId: string): Promise<StudyPlan> {
  const res = await apiClient.get(`/books/${bookId}/plan`);
  return res.data;
}
```

### 2. Book detail screen — `app/books/[bookId].tsx`

This screen has two sections: profile summary and study plan.

**Profile section:**

```text
┌──────────────────────────────┐
│  📘 Linear Algebra Ch. 2     │
│                              │
│  Subject: Linear Algebra     │
│  Level: Undergraduate        │
│  Style: Definition-Theorem   │
│  Proof Density: Medium       │
│                              │
│  18 tidbits · ~4.5 hours     │
│  Progress: 32%               │
│  ════════════░░░░░░░░░░░░░░  │
└──────────────────────────────┘
```

**Study plan section (scrollable list):**

```text
┌──────────────────────────────┐
│  Day 1 · Vectors             │
│  ✅ Completed · 15 min       │
├──────────────────────────────┤
│  Day 2 · Scalar Mult.        │
│  ✅ Completed · 10 min       │
├──────────────────────────────┤
│  Day 3 · Linear Combination  │
│  🔵 Available · 15 min       │  ← tap to open
├──────────────────────────────┤
│  Review · Vectors Review     │
│  🟡 Review · 10 min          │  ← inserted, visually distinct
├──────────────────────────────┤
│  Day 4 · Span                │
│  🔒 Locked · 20 min          │
├──────────────────────────────┤
│  ...                         │
└──────────────────────────────┘
```

### 3. Tidbit roadmap item component — `src/components/TidbitRoadmapItem.tsx`

```typescript
interface TidbitRoadmapItemProps {
  tidbit: Tidbit;
  progress: UserTidbitProgress | null;
  onPress: () => void;
}
```

Visual rules:
- **Completed**: green checkmark, muted colors.
- **Available**: primary color, bold, tappable.
- **Locked**: gray, lock icon, not tappable.
- **Review/Remedial** (non-original): different background tint, "Review" or "Remedial" badge.

### 4. Progress bar component — `src/components/ProgressBar.tsx`

Animated horizontal progress bar showing `completed / total` tidbits.

### 5. Custom hook — `src/hooks/useBook.ts` (extend)

```typescript
export function useStudyPlan(bookId: string) {
  return useQuery({
    queryKey: ["study-plan", bookId],
    queryFn: () => getStudyPlan(bookId),
    enabled: !!bookId,
  });
}
```

---

## Files to Create/Modify

```text
app/books/[bookId].tsx          (replace placeholder)
src/components/TidbitRoadmapItem.tsx
src/components/ProgressBar.tsx
src/hooks/useBook.ts            (extend)
src/api/books.ts                (extend)
```

---

## Acceptance Criteria

- [ ] Book detail screen shows detected subject, level, style, proof density.
- [ ] Study plan renders as an ordered list of tidbits.
- [ ] Tidbit status (locked/available/completed) is visually distinct.
- [ ] Review/remedial tidbits are visually distinct from original plan tidbits.
- [ ] Tapping an available tidbit navigates to `tidbits/[tidbitId]`.
- [ ] Locked tidbits are not tappable.
- [ ] Progress bar accurately reflects completion.

---

## Agent Prompt

```text
Build book profile and study plan UI for MathPath:

1. app/books/[bookId].tsx — shows book profile (subject, level, style, proof density, progress bar) and scrollable tidbit roadmap.

2. src/components/TidbitRoadmapItem.tsx — renders a single tidbit in the roadmap with status icon (completed/available/locked), title, estimated time, and visual distinction for review/remedial types.

3. src/components/ProgressBar.tsx — animated horizontal bar.

4. Extend src/hooks/useBook.ts with useStudyPlan hook.

5. Extend src/api/books.ts with getStudyPlan.

Use theme tokens. Completed=green, available=primary, locked=gray. Review/remedial items have a yellow/orange tint.
```
