# F01 — Expo App Skeleton

> **Objective:** Create a React Native + Expo project with navigation, API client, theming, and placeholder screens for all routes.

**Depends on:** Backend API contracts defined (B01 health endpoint for connectivity test)

---

## Tasks

### 1. Initialize Expo project

```bash
npx create-expo-app mathpath-mobile --template blank-typescript
cd mathpath-mobile
npx expo install expo-router expo-linking expo-constants expo-status-bar
```

### 2. Configure Expo Router

Set up file-based routing in `app/`:

```text
mobile/
  app/
    _layout.tsx          → Root layout (navigation container, theme provider)
    index.tsx            → Home / entry redirect
    onboarding.tsx       → Onboarding screen (placeholder)
    upload.tsx           → Upload screen (placeholder)
    books/
      index.tsx          → Books list (placeholder)
      [bookId].tsx       → Book detail / study plan (placeholder)
    tidbits/
      [tidbitId].tsx     → Tidbit lesson screen (placeholder)
      [tidbitId]/
        quiz.tsx         → Quiz screen (placeholder)
        ask.tsx          → Ask question screen (placeholder)
    progress.tsx         → Progress dashboard (placeholder)
    settings.tsx         → Settings (placeholder)
```

### 3. Root layout — `app/_layout.tsx`

```tsx
export default function RootLayout() {
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <Stack>
          <Stack.Screen name="index" options={{ headerShown: false }} />
          <Stack.Screen name="onboarding" options={{ title: "Welcome" }} />
          <Stack.Screen name="upload" options={{ title: "Upload" }} />
          <Stack.Screen name="books/index" options={{ title: "My Books" }} />
          <Stack.Screen name="progress" options={{ title: "Progress" }} />
        </Stack>
      </QueryClientProvider>
    </ThemeProvider>
  );
}
```

### 4. API client — `src/api/client.ts`

```typescript
import axios from "axios";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

export async function healthCheck(): Promise<boolean> {
  const res = await apiClient.get("/health");
  return res.data.status === "ok";
}
```

### 5. TanStack Query setup — `src/api/queryClient.ts`

```typescript
import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 2, staleTime: 5 * 60 * 1000 },
  },
});
```

### 6. Theme / design tokens — `src/theme/index.ts`

```typescript
export const theme = {
  colors: {
    primary: "#4F46E5",
    secondary: "#7C3AED",
    background: "#FAFAFA",
    surface: "#FFFFFF",
    text: "#1F2937",
    textSecondary: "#6B7280",
    success: "#10B981",
    warning: "#F59E0B",
    error: "#EF4444",
    border: "#E5E7EB",
  },
  spacing: { xs: 4, sm: 8, md: 16, lg: 24, xl: 32 },
  borderRadius: { sm: 8, md: 12, lg: 16 },
  fontSize: { sm: 14, md: 16, lg: 20, xl: 28 },
};
```

### 7. Type definitions — `src/types/api.ts`

```typescript
export interface Book {
  id: string;
  title: string;
  source_type: string;
  status: string;
  created_at: string;
}

export interface BookProfile { ... }
export interface StudyPlan { ... }
export interface Tidbit { ... }
export interface TidbitDetail { ... }
export interface Lesson { ... }
export interface Quiz { ... }
export interface GradingResponse { ... }
export interface ProgressDashboard { ... }
```

Define all types matching the backend JSON contracts from the plan.

### 8. Tab/bottom navigation

For MVP use a simple bottom tab or stack navigation:

```text
Tabs:
  - Home (current tidbit)
  - Books (book list)
  - Progress (dashboard)
  - Settings
```

### 9. Install core dependencies

```bash
npx expo install @tanstack/react-query
npm install axios zustand
npx expo install expo-document-picker expo-av expo-notifications
```

---

## Files to Create

```text
mobile/
  app/_layout.tsx
  app/index.tsx
  app/onboarding.tsx
  app/upload.tsx
  app/books/index.tsx
  app/books/[bookId].tsx
  app/tidbits/[tidbitId].tsx
  app/tidbits/[tidbitId]/quiz.tsx
  app/tidbits/[tidbitId]/ask.tsx
  app/progress.tsx
  app/settings.tsx
  src/api/client.ts
  src/api/queryClient.ts
  src/types/api.ts
  src/theme/index.ts
```

---

## Acceptance Criteria

- [ ] `npx expo start` launches without errors.
- [ ] Can navigate between Upload, Books, Tidbit, Progress, Settings.
- [ ] API client can call backend `/health` and receive `{"status": "ok"}`.
- [ ] TanStack Query is wired and functional.
- [ ] All placeholder screens render with screen name text.

---

## Agent Prompt

```text
Create a React Native + Expo project at mathpath/mobile/ with:
- Expo Router file-based navigation (app/ directory)
- Screens: index, onboarding, upload, books/index, books/[bookId], tidbits/[tidbitId], tidbits/[tidbitId]/quiz, tidbits/[tidbitId]/ask, progress, settings
- src/api/client.ts with axios-based API client and healthCheck()
- src/api/queryClient.ts with TanStack Query setup
- src/types/api.ts with TypeScript interfaces matching backend contracts
- src/theme/index.ts with design tokens
- Root _layout.tsx with Stack navigator, QueryClientProvider, ThemeProvider
- Bottom tab navigation for Home, Books, Progress, Settings
All screens should be placeholder shells for now.
```
