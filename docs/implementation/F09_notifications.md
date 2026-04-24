# F09 — Push Notifications

> **Objective:** Register for push notifications, save the token to the backend, schedule daily study reminders, and deep-link to the current tidbit on tap.

**Depends on:** F01 (skeleton), Backend endpoint for push token storage

---

## Tasks

### 1. Notification registration — `src/utils/notifications.ts`

```typescript
import * as Notifications from "expo-notifications";
import * as Device from "expo-device";
import { Platform } from "react-native";

export async function registerForPushNotifications(): Promise<string | null> {
  if (!Device.isDevice) return null;

  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== "granted") {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== "granted") return null;

  const token = (await Notifications.getExpoPushTokenAsync()).data;

  if (Platform.OS === "android") {
    Notifications.setNotificationChannelAsync("study-reminders", {
      name: "Study Reminders",
      importance: Notifications.AndroidImportance.HIGH,
    });
  }

  return token;
}

export async function scheduleDailyReminder(hour: number = 9, minute: number = 0) {
  await Notifications.cancelAllScheduledNotificationsAsync();
  await Notifications.scheduleNotificationAsync({
    content: {
      title: "Time to study!",
      body: "Your next tidbit is waiting.",
      data: { screen: "current-tidbit" },
    },
    trigger: {
      type: "daily",
      hour,
      minute,
    },
  });
}
```

### 2. Save push token to backend

```typescript
export async function savePushToken(token: string): Promise<void> {
  await apiClient.post("/notifications/register", { push_token: token });
}
```

### 3. Notification handler in root layout — `app/_layout.tsx`

```typescript
useEffect(() => {
  const subscription = Notifications.addNotificationResponseReceivedListener((response) => {
    const data = response.notification.request.content.data;
    if (data.screen === "current-tidbit") {
      router.push("/tidbits/current");
    }
  });
  return () => subscription.remove();
}, []);
```

### 4. Settings screen integration — `app/settings.tsx`

```text
Reminder Settings:
- Toggle: Daily reminder [ON/OFF]
- Time picker: Reminder time [9:00 AM]
- Test notification button
```

### 5. Backend endpoint (lightweight)

```python
@router.post("/notifications/register")
async def register_push_token(data: PushTokenCreate, db = Depends(get_db)):
    # Store user's push token
    ...
```

---

## Files to Create/Modify

```text
src/utils/notifications.ts
app/_layout.tsx                (extend with notification handler)
app/settings.tsx               (replace placeholder with reminder settings)
```

---

## Acceptance Criteria

- [ ] Push notification permission is requested on first launch.
- [ ] Push token is saved to backend.
- [ ] Daily reminder notification fires at configured time.
- [ ] Tapping notification opens the current tidbit.
- [ ] Settings screen allows toggling reminders and changing time.
- [ ] Test notification button works in settings.

---

## Agent Prompt

```text
Add push notifications to MathPath:

1. src/utils/notifications.ts — registerForPushNotifications (get expo push token), scheduleDailyReminder (local scheduled notification), savePushToken (send to backend).

2. Extend app/_layout.tsx — listen for notification taps, deep-link to current tidbit.

3. app/settings.tsx — reminder toggle, time picker, test notification button.

4. Register push token on app launch and save to backend.
```
