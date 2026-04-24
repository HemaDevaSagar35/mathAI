# F05 — Ask Question UI

> **Objective:** Allow users to ask free-form questions under the current tidbit. Show AI answers grounded in the textbook. Persist and display Q&A history.

**Depends on:** F01 (skeleton), Backend B09 (lessons for context), API endpoint for tidbit questions

---

## Tasks

### 1. API functions — `src/api/tidbits.ts` (extend)

```typescript
export async function askQuestion(tidbitId: string, question: string): Promise<QuestionAnswer> {
  const res = await apiClient.post(`/tidbits/${tidbitId}/questions`, { question });
  return res.data;
}

export async function getQuestions(tidbitId: string): Promise<QuestionAnswer[]> {
  const res = await apiClient.get(`/tidbits/${tidbitId}/questions`);
  return res.data;
}
```

### 2. Ask question screen — `app/tidbits/[tidbitId]/ask.tsx`

```text
┌──────────────────────────────┐
│  Ask about: Span             │
│                              │
│  Previous Q&A                │
│  ┌────────────────────────┐  │
│  │ Q: Why is span ≠ basis?│  │
│  │ A: Span can have...    │  │
│  │ 📖 Based on p.21-22    │  │
│  └────────────────────────┘  │
│  ┌────────────────────────┐  │
│  │ Q: Can one vector...   │  │
│  │ A: A single nonzero... │  │
│  └────────────────────────┘  │
│                              │
│  ┌────────────────────────┐  │
│  │ Type your question...  │  │
│  │                    [→] │  │
│  └────────────────────────┘  │
│                              │
│  Loading spinner when        │
│  waiting for answer          │
└──────────────────────────────┘
```

### 3. Q&A card component

```typescript
interface QACardProps {
  question: string;
  answer: string;
  grounding?: { source_chunk_ids: string[]; page_refs?: number[] };
}
```

Show grounding info (page references) to reinforce textbook connection.

### 4. Input behavior

- Text input at the bottom of the screen.
- Submit on Enter or tap send button.
- Show loading spinner while waiting.
- New Q&A appears at the bottom of the list.
- Scroll to bottom when new answer arrives.

---

## Files to Create/Modify

```text
app/tidbits/[tidbitId]/ask.tsx    (replace placeholder)
src/api/tidbits.ts                (extend)
```

---

## Acceptance Criteria

- [ ] User can type and submit a question.
- [ ] Answer is displayed with grounding references.
- [ ] Previous Q&A for this tidbit loads on screen open.
- [ ] Loading state shown while waiting for AI answer.
- [ ] Q&A persists across screen navigations.

---

## Agent Prompt

```text
Build ask-question UI for MathPath:

1. app/tidbits/[tidbitId]/ask.tsx — screen with previous Q&A list and text input. Submit question, show loading, display answer with grounding info.

2. Extend src/api/tidbits.ts with askQuestion and getQuestions.

3. Q&A card shows question, answer, and page references.

Text input at bottom, auto-scroll to new answers. Mobile-friendly keyboard handling.
```
