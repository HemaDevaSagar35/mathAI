# F07 — Voice Recording & Transcript Flow

> **Objective:** Add voice recording to the quiz flow. Record audio, show waveform, transcribe, allow editing, then submit edited transcript for grading.

**Depends on:** F06 (quiz UI), Backend speech-to-text or client-side transcription

---

## Tasks

### 1. Voice recorder component — `src/components/VoiceRecorder.tsx`

```typescript
interface VoiceRecorderProps {
  onTranscriptReady: (transcript: string, audioUri: string) => void;
  isRecording: boolean;
}
```

UI:

```text
┌──────────────────────────────┐
│                              │
│        [🎤 Hold to Record]   │  ← idle
│                              │
│  ──── Recording... 0:05 ──── │  ← recording (with waveform)
│        [⏹ Release to Stop]   │
│                              │
│  ──── Transcribing... ─────  │  ← processing
│                              │
│  Transcript:                 │
│  ┌────────────────────────┐  │
│  │ Span is all the linear │  │  ← editable
│  │ combinations of given  │  │
│  │ vectors               │  │
│  └────────────────────────┘  │
│  [🔄 Re-record] [Submit →]  │
│                              │
└──────────────────────────────┘
```

### 2. Voice recording hook — `src/hooks/useVoiceRecording.ts`

```typescript
export function useVoiceRecording() {
  const [isRecording, setIsRecording] = useState(false);
  const [audioUri, setAudioUri] = useState<string | null>(null);
  const [transcript, setTranscript] = useState<string | null>(null);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const recordingRef = useRef<Audio.Recording | null>(null);

  async function startRecording(): Promise<void> {
    await Audio.requestPermissionsAsync();
    await Audio.setAudioModeAsync({ allowsRecordingIOS: true, playsInSilentModeIOS: true });
    const recording = new Audio.Recording();
    await recording.prepareToRecordAsync(Audio.RecordingOptionsPresets.HIGH_QUALITY);
    await recording.startAsync();
    recordingRef.current = recording;
    setIsRecording(true);
  }

  async function stopRecording(): Promise<string> {
    // Stop recording, get URI, transcribe
  }

  async function transcribe(uri: string): Promise<string> {
    // Send audio to backend or use client-side transcription
  }

  return { isRecording, audioUri, transcript, isTranscribing, startRecording, stopRecording, setTranscript };
}
```

### 3. Transcription API

Option A: Backend transcription

```typescript
export async function transcribeAudio(audioUri: string): Promise<string> {
  const formData = new FormData();
  formData.append("audio", { uri: audioUri, name: "answer.m4a", type: "audio/m4a" } as any);
  const res = await apiClient.post("/transcribe", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data.transcript;
}
```

Option B: Client-side using Whisper API directly (for MVP, backend transcription is simpler).

### 4. Integrate into quiz flow

Modify quiz screen to toggle between typed and voice input:

```text
Answer Mode: [Typed] [Voice]
```

When voice is selected, show VoiceRecorder instead of text input. After recording + transcription, the editable transcript feeds into the same grading flow.

### 5. Audio permissions

Request microphone permission on first use:

```typescript
const { status } = await Audio.requestPermissionsAsync();
if (status !== "granted") {
  // Show explanation and settings link
}
```

---

## Files to Create/Modify

```text
src/components/VoiceRecorder.tsx
src/hooks/useVoiceRecording.ts
app/tidbits/[tidbitId]/quiz.tsx     (extend with voice mode toggle)
```

---

## Acceptance Criteria

- [ ] User can record audio answer.
- [ ] Recording shows duration indicator.
- [ ] After stopping, audio is transcribed.
- [ ] Transcript is shown in an editable text field.
- [ ] User can edit the transcript before submitting.
- [ ] "Re-record" button works.
- [ ] Edited transcript is sent to the same grading endpoint.
- [ ] Grading works identically for voice and typed inputs.
- [ ] Microphone permission is handled gracefully.
- [ ] Fallback to typed input if audio is unavailable.

---

## Agent Prompt

```text
Add voice recording to MathPath quiz:

1. src/components/VoiceRecorder.tsx — record button (hold to record), recording indicator with duration, transcription loading, editable transcript display, re-record and submit buttons.

2. src/hooks/useVoiceRecording.ts — manages recording lifecycle with expo-av. Start/stop recording, get audio URI, send for transcription, allow transcript editing.

3. Extend app/tidbits/[tidbitId]/quiz.tsx — add toggle between typed and voice modes. Voice mode uses VoiceRecorder, then feeds transcript into same grading flow.

4. Handle microphone permissions gracefully with fallback to typed input.
```
