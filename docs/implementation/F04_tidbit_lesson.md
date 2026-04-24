# F04 — Tidbit Lesson UI

> **Objective:** Render the full lesson for a tidbit using collapsible cards: layered explanations, intuition bridge, worked examples, proof ladder, care notes, memory hooks.

**Depends on:** F01 (skeleton), Backend B09 (lessons), B10 (proof ladder)

---

## Tasks

### 1. API functions — `src/api/tidbits.ts`

```typescript
export async function getTidbit(tidbitId: string): Promise<TidbitDetail> {
  const res = await apiClient.get(`/tidbits/${tidbitId}`);
  return res.data;
}

export async function generateLesson(tidbitId: string): Promise<Lesson> {
  const res = await apiClient.post(`/tidbits/${tidbitId}/lesson/generate`);
  return res.data;
}
```

### 2. Tidbit lesson screen — `app/tidbits/[tidbitId].tsx`

Scrollable screen with collapsible card sections:

```text
┌──────────────────────────────┐
│  Span as Reachability        │  ← title
│  Core: Span is the set of... │  ← core_idea (always visible)
├──────────────────────────────┤
│  ▸ Why It Matters            │  ← collapsible
├──────────────────────────────┤
│  ▸ Simple Explanation        │  ← explain_like_10th_grader
├──────────────────────────────┤
│  ▸ Engineer's View           │  ← explain_like_engineer
├──────────────────────────────┤
│  ▸ Formal Treatment          │  ← explain_like_math_mature
├──────────────────────────────┤
│  ▸ Intuition Bridge          │  ← simple → math → formal
├──────────────────────────────┤
│  ▸ Formal Definition         │  ← with math rendering
├──────────────────────────────┤
│  ▸ Worked Examples (2)       │  ← expandable list
├──────────────────────────────┤
│  ▸ Common Mistakes (2)       │
├──────────────────────────────┤
│  ▸ Proof Ladder              │  ← only if exists
├──────────────────────────────┤
│  ▸ Care Notes (3)            │
├──────────────────────────────┤
│  ▸ Real-World Connections    │
├──────────────────────────────┤
│  Memory Hooks                │  ← always visible
│  • "Span = reachability"     │
├──────────────────────────────┤
│  Quick Summary               │  ← always visible
│  "Span tells you everything  │
│   a set of vectors can..."   │
├──────────────────────────────┤
│  [Ask a Question]  [Quiz →]  │  ← action buttons
└──────────────────────────────┘
```

### 3. LessonCard component — `src/components/LessonCard.tsx`

```typescript
interface LessonCardProps {
  title: string;
  children: React.ReactNode;
  defaultExpanded?: boolean;
  icon?: string;
}
```

Collapsible card with animated expand/collapse. Title row is always visible and tappable.

### 4. MathText component — `src/components/MathText.tsx`

```typescript
interface MathTextProps {
  content: string;
}
```

Renders math notation. Options:
- `react-native-math-view` for native rendering.
- WebView + KaTeX as fallback.
- For MVP, use a WebView with KaTeX that renders LaTeX strings.

### 5. ProofLadder component — `src/components/ProofLadder.tsx`

Progressive reveal: user taps to expand each level.

```text
Level 0: Intuition          ✓ (always shown)
Level 1: Proof Sketch       ▸ (tap to reveal)
Level 2: Guided Proof       ▸
Level 3: Formal Proof       ▸
Level 4: Commentary         ▸
```

Each level stays open once revealed. Guided proof shows step-by-step with prompts.

### 6. CareNoteList component — `src/components/CareNoteList.tsx`

```typescript
interface CareNoteListProps {
  notes: CareNote[];
}
```

Color-coded by type:
- `misconception` → red/orange
- `warning` → amber
- `bridge` → blue
- `memory_hook` → green
- `application` → purple
- `exam_trap` → red
- `future_use` → gray

### 7. Hook — `src/hooks/useTidbit.ts`

```typescript
export function useTidbit(tidbitId: string) {
  return useQuery({
    queryKey: ["tidbit", tidbitId],
    queryFn: () => getTidbit(tidbitId),
    enabled: !!tidbitId,
  });
}
```

---

## Files to Create/Modify

```text
src/api/tidbits.ts
src/hooks/useTidbit.ts
src/components/LessonCard.tsx
src/components/MathText.tsx
src/components/ProofLadder.tsx
src/components/CareNoteList.tsx
app/tidbits/[tidbitId].tsx       (replace placeholder)
```

---

## Acceptance Criteria

- [ ] Tidbit screen loads and displays lesson content.
- [ ] Collapsible cards expand/collapse smoothly.
- [ ] Core idea, memory hooks, and quick summary are always visible.
- [ ] Math notation renders correctly (LaTeX via KaTeX/WebView).
- [ ] Proof ladder reveals levels progressively.
- [ ] Care notes are color-coded by type.
- [ ] "Ask a Question" button navigates to ask screen.
- [ ] "Start Quiz" button navigates to quiz screen.
- [ ] Long content is scrollable and readable on mobile.

---

## Agent Prompt

```text
Build tidbit lesson UI for MathPath:

1. src/api/tidbits.ts — getTidbit, generateLesson.
2. src/hooks/useTidbit.ts — useTidbit hook.
3. app/tidbits/[tidbitId].tsx — scrollable screen with collapsible LessonCard sections for each lesson part. Core idea, memory hooks, summary always visible. Action buttons for quiz and ask.
4. src/components/LessonCard.tsx — collapsible card with animated expand/collapse.
5. src/components/MathText.tsx — render LaTeX using WebView+KaTeX.
6. src/components/ProofLadder.tsx — progressive 5-level reveal.
7. src/components/CareNoteList.tsx — color-coded care notes by type.

Use theme tokens. Prioritize readability on small screens. No wall of text — everything collapsible.
```
