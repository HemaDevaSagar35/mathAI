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
    connect.tsx          → Server connection screen (FIRST screen for new users)
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

### 4. Server connection screen — `app/connect.tsx`

This is the **first screen** a new user sees. It connects the phone to the self-hosted backend.

```text
┌──────────────────────────────┐
│                              │
│       ◈ MathPath             │
│                              │
│  Connect to your server      │
│                              │
│  Run `docker compose up` on  │
│  your computer, then enter   │
│  the IP shown in the         │
│  terminal below.             │
│                              │
│  Server URL:                 │
│  ┌────────────────────────┐  │
│  │ http://192.168.1.42:80 │  │
│  └────────────────────────┘  │
│                              │
│         [Connect]            │
│                              │
│  ● Checking...               │
│  ✓ Connected!                │
│  ✗ Can't reach server        │
│                              │
└──────────────────────────────┘
```

Behavior:
1. On first launch, if no saved server URL → show this screen.
2. User enters URL (e.g., `http://192.168.1.42:8000`).
3. App calls `GET {url}/api/health`.
4. On success → save URL to AsyncStorage → navigate to main app.
5. On failure → show error with troubleshooting tips.
6. On subsequent launches → skip this screen (URL already saved).
7. URL is changeable from Settings screen.

### 5. API client with dynamic URL — `src/api/client.ts`

The API client reads the server URL from a Zustand store (backed by AsyncStorage), not a hardcoded env var.

```typescript
import axios, { AxiosInstance } from "axios";
import { useServerStore } from "../stores/serverStore";

let _client: AxiosInstance | null = null;

export function getApiClient(): AxiosInstance {
  const serverUrl = useServerStore.getState().serverUrl;
  if (!serverUrl) throw new Error("Server URL not configured");

  if (!_client || _client.defaults.baseURL !== serverUrl) {
    _client = axios.create({
      baseURL: serverUrl,
      timeout: 30000,
      headers: { "Content-Type": "application/json" },
    });
  }
  return _client;
}

export async function healthCheck(url: string): Promise<boolean> {
  try {
    const res = await axios.get(`${url}/api/health`, { timeout: 5000 });
    return res.data?.status === "ok";
  } catch {
    return false;
  }
}
```

### 6. Server store — `src/stores/serverStore.ts`

```typescript
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import AsyncStorage from "@react-native-async-storage/async-storage";

interface ServerState {
  serverUrl: string | null;
  isConnected: boolean;
  setServerUrl: (url: string) => void;
  clearServerUrl: () => void;
}

export const useServerStore = create<ServerState>()(
  persist(
    (set) => ({
      serverUrl: null,
      isConnected: false,
      setServerUrl: (url) => set({ serverUrl: url, isConnected: true }),
      clearServerUrl: () => set({ serverUrl: null, isConnected: false }),
    }),
    {
      name: "mathpath-server",
      storage: createJSONStorage(() => AsyncStorage),
    }
  )
);
```

### 7. TanStack Query setup — `src/api/queryClient.ts`

```typescript
import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 2, staleTime: 5 * 60 * 1000 },
  },
});
```

### 8. Theme / design tokens — `src/theme/index.ts`

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

### 9. Type definitions — `src/types/api.ts`

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

### 10. Entry redirect — `app/index.tsx`

```typescript
export default function Index() {
  const serverUrl = useServerStore((s) => s.serverUrl);

  useEffect(() => {
    if (!serverUrl) {
      router.replace("/connect");
    } else {
      router.replace("/books");
    }
  }, [serverUrl]);

  return <LoadingSpinner />;
}
```

If no server URL is saved, redirect to connect screen. Otherwise, go to the main app.

### 11. Tab/bottom navigation

For MVP use a simple bottom tab or stack navigation:

```text
Tabs:
  - Home (current tidbit)
  - Books (book list)
  - Progress (dashboard)
  - Settings
```

### 12. Install core dependencies

```bash
npx expo install @tanstack/react-query @react-native-async-storage/async-storage
npm install axios zustand
npx expo install expo-document-picker expo-av expo-notifications
```

---

## Files to Create

```text
mobile/
  app/_layout.tsx
  app/index.tsx
  app/connect.tsx            ← NEW: server connection screen
  app/onboarding.tsx
  app/upload.tsx
  app/books/index.tsx
  app/books/[bookId].tsx
  app/tidbits/[tidbitId].tsx
  app/tidbits/[tidbitId]/quiz.tsx
  app/tidbits/[tidbitId]/ask.tsx
  app/progress.tsx
  app/settings.tsx
  src/api/client.ts          ← CHANGED: dynamic URL from store
  src/api/queryClient.ts
  src/stores/serverStore.ts  ← NEW: persisted server URL
  src/types/api.ts
  src/theme/index.ts
```

---

## Acceptance Criteria

- [ ] `npx expo start` launches without errors.
- [ ] First launch shows server connection screen.
- [ ] Entering a valid server URL and tapping Connect → health check passes → navigates to main app.
- [ ] Server URL persists across app restarts (AsyncStorage).
- [ ] Entering an invalid URL shows a clear error.
- [ ] Can navigate between Upload, Books, Tidbit, Progress, Settings.
- [ ] API client uses the saved server URL for all requests.
- [ ] TanStack Query is wired and functional.
- [ ] Settings screen shows current server URL with option to change it.
- [ ] All placeholder screens render with screen name text.

---

## Agent Prompt

```text
Create a React Native + Expo project at mathpath/mobile/ with:
- Expo Router file-based navigation (app/ directory)
- Screens: index, connect, onboarding, upload, books/index, books/[bookId], tidbits/[tidbitId], tidbits/[tidbitId]/quiz, tidbits/[tidbitId]/ask, progress, settings
- app/connect.tsx — server connection screen: URL input, health check, save to AsyncStorage, navigate on success. Show clear instructions about running docker compose up.
- app/index.tsx — checks for saved server URL, redirects to /connect or /books.
- src/stores/serverStore.ts — Zustand store with AsyncStorage persistence for serverUrl.
- src/api/client.ts — dynamic axios client that reads URL from serverStore (NOT hardcoded env var).
- src/api/queryClient.ts with TanStack Query setup
- src/types/api.ts with TypeScript interfaces matching backend contracts
- src/theme/index.ts with design tokens
- Root _layout.tsx with Stack navigator, QueryClientProvider, ThemeProvider
- Bottom tab navigation for Home, Books, Progress, Settings
- Settings screen shows current server URL with option to change/disconnect.
All non-connect screens should be placeholder shells for now.
```
