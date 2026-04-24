# F06 — Quiz Transcript UI

> **Objective:** Build the typed-transcript quiz flow: show questions one at a time, accept text answers, submit for grading, show feedback, advance through all questions.

**Depends on:** F01 (skeleton), Backend B11 (quiz), B12 (grading)

---

## Tasks

### 1. API functions — `src/api/quizzes.ts`

```typescript
export async function getQuiz(tidbitId: string): Promise<Quiz> {
  const res = await apiClient.get(`/tidbits/${tidbitId}/quiz`);
  return res.data;
}

export async function generateQuiz(tidbitId: string): Promise<Quiz> {
  const res = await apiClient.post(`/tidbits/${tidbitId}/quiz/generate`);
  return res.data;
}
```

### 2. Grading API — `src/api/grading.ts`

```typescript
export async function gradeTranscript(
  tidbitId: string,
  questionId: string,
  transcript: string
): Promise<GradingResponse> {
  const res = await apiClient.post(`/tidbits/${tidbitId}/quiz/grade`, {
    question_id: questionId,
    transcript_final: transcript,
  });
  return res.data;
}
```

### 3. Quiz screen — `app/tidbits/[tidbitId]/quiz.tsx`

Flow: question → answer → grade → feedback → next question → summary.

**Question state:**

```text
┌──────────────────────────────┐
│  Question 1 of 4             │
│  ━━━━━━━━░░░░░░░░░░░░░░░░░  │
│                              │
│  What does span mean in      │
│  your own words?             │
│                              │
│  ┌────────────────────────┐  │
│  │                        │  │
│  │  Type your answer...   │  │
│  │                        │  │
│  └────────────────────────┘  │
│                              │
│         [Submit Answer]      │
└──────────────────────────────┘
```

**Feedback state:**

```text
┌──────────────────────────────┐
│  Question 1 of 4             │
│                              │
│  Score: 75%  ● Mostly Correct│
│                              │
│  Feedback:                   │
│  Good answer. You correctly  │
│  said span involves combos.  │
│  Mention scalar mult. too.   │
│                              │
│  Missing:                    │
│  • Scalar multiplication     │
│                              │
│  Follow-up to think about:   │
│  Can one vector span R²?     │
│                              │
│         [Next Question →]    │
└──────────────────────────────┘
```

**Summary state (after all questions):**

```text
┌──────────────────────────────┐
│  Quiz Complete!              │
│                              │
│  Overall Score: 72%          │
│  ━━━━━━━━━━━━━━━░░░░░░░░░░  │
│                              │
│  Q1: 75% ● Mostly Correct   │
│  Q2: 90% ● Correct          │
│  Q3: 50% ● Partially        │
│  Q4: 72% ● Mostly Correct   │
│                              │
│  Next: Continue to Day 4     │
│                              │
│   [Back to Lesson]  [Next →] │
└──────────────────────────────┘
```

### 4. QuizQuestion component — `src/components/QuizQuestion.tsx`

```typescript
interface QuizQuestionProps {
  question: QuizQuestionData;
  questionNumber: number;
  totalQuestions: number;
  onSubmit: (transcript: string) => void;
  isSubmitting: boolean;
}
```

### 5. QuizFeedback component

```typescript
interface QuizFeedbackProps {
  grading: GradingResponse;
  onNext: () => void;
  isLast: boolean;
}
```

Color-code by correctness:
- `correct` → green
- `mostly_correct` → light green
- `partially_correct` → amber
- `incorrect` → red

### 6. Quiz state management

Use local state (useState or zustand) to track:

```typescript
interface QuizState {
  currentIndex: number;
  answers: Map<string, { transcript: string; grading: GradingResponse }>;
  phase: "question" | "grading" | "feedback" | "summary";
}
```

---

## Files to Create/Modify

```text
src/api/quizzes.ts
src/api/grading.ts
src/components/QuizQuestion.tsx
app/tidbits/[tidbitId]/quiz.tsx    (replace placeholder)
```

---

## Acceptance Criteria

- [ ] Quiz loads and shows first question.
- [ ] User can type answer and submit.
- [ ] Loading state during grading.
- [ ] Feedback screen shows score, correctness, feedback, missing points.
- [ ] "Next Question" advances to next question.
- [ ] Summary screen shows all scores after final question.
- [ ] Summary shows recommended next action (continue/review/remedial).

---

## Agent Prompt

```text
Build quiz transcript UI for MathPath:

1. src/api/quizzes.ts — getQuiz, generateQuiz.
2. src/api/grading.ts — gradeTranscript.
3. app/tidbits/[tidbitId]/quiz.tsx — full quiz flow: show question, text input, submit, show feedback, next question, final summary. Track state with currentIndex, answers map, phase.
4. src/components/QuizQuestion.tsx — question display with text input and submit button.
5. Color-code feedback by correctness. Show missing points and follow-up questions.
6. Summary screen with overall score and next action recommendation.
```
