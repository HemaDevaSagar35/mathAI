# F02 — Books & Upload UI

> **Objective:** Build the book upload flow (PDF picker, upload progress, processing status) and the books list screen.

**Depends on:** F01 (skeleton), Backend B14 (upload endpoint), B15 (process endpoint)

---

## Tasks

### 1. API functions — `src/api/books.ts`

```typescript
export async function uploadBookPdf(file: DocumentPickerAsset): Promise<{ book_id: string; status: string }> {
  const formData = new FormData();
  formData.append("file", {
    uri: file.uri,
    name: file.name,
    type: file.mimeType || "application/pdf",
  } as any);
  const res = await apiClient.post("/books/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export async function processBook(bookId: string, steps?: string[]): Promise<{ status: string }> {
  const res = await apiClient.post(`/books/${bookId}/process`, { steps });
  return res.data;
}

export async function getBooks(): Promise<Book[]> {
  const res = await apiClient.get("/books");
  return res.data;
}

export async function getBookProfile(bookId: string): Promise<BookProfile> {
  const res = await apiClient.get(`/books/${bookId}/profile`);
  return res.data;
}
```

### 2. Upload screen — `app/upload.tsx`

States: `idle` → `picking` → `uploading` → `uploaded` → `processing` → `processed` → `failed`

```text
UI Elements:
- Large "Upload Math Textbook" title
- Upload area with tap-to-pick or drag-and-drop visual
- File name display after picking
- Upload progress bar
- Processing spinner with status text
- "View Study Plan" button after processing completes
- Error state with retry button
```

Flow:
1. User taps upload area → `expo-document-picker` opens.
2. File selected → show file name, start upload.
3. Upload completes → trigger `processBook()`.
4. Poll for status or wait for response.
5. Processing done → navigate to `books/[bookId]`.

### 3. Books list screen — `app/books/index.tsx`

```text
UI Elements:
- List of uploaded books
- Each card shows:
  - Book title
  - Status badge (processing, processed, failed)
  - Progress percentage (if study plan exists)
  - Current tidbit name
  - Detected subject badge
- FAB or "+" button to upload new book
- Pull-to-refresh
- Empty state: "No books yet. Upload your first textbook!"
```

### 4. Upload utility — `src/utils/upload.ts`

```typescript
export async function pickDocument(): Promise<DocumentPickerAsset | null> {
  const result = await DocumentPicker.getDocumentAsync({
    type: "application/pdf",
    copyToCacheDirectory: true,
  });
  if (result.canceled) return null;
  return result.assets[0];
}
```

### 5. Custom hook — `src/hooks/useBook.ts`

```typescript
export function useBooks() {
  return useQuery({ queryKey: ["books"], queryFn: getBooks });
}

export function useBookProfile(bookId: string) {
  return useQuery({
    queryKey: ["book-profile", bookId],
    queryFn: () => getBookProfile(bookId),
    enabled: !!bookId,
  });
}

export function useUploadBook() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: uploadBookPdf,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["books"] }),
  });
}
```

---

## Files to Create/Modify

```text
src/api/books.ts
src/utils/upload.ts
src/hooks/useBook.ts
app/upload.tsx          (replace placeholder)
app/books/index.tsx     (replace placeholder)
```

---

## Acceptance Criteria

- [ ] User can pick a PDF from the device.
- [ ] PDF uploads to the backend successfully.
- [ ] Upload progress is visible.
- [ ] Processing state is shown after upload.
- [ ] After processing, user is navigated to the book detail.
- [ ] Books list shows all uploaded books with status.
- [ ] Pull-to-refresh works on books list.
- [ ] Error state shows retry option.

---

## Agent Prompt

```text
Build upload and books list UI for MathPath mobile:

1. src/api/books.ts — uploadBookPdf (multipart), processBook, getBooks, getBookProfile.
2. src/utils/upload.ts — pickDocument using expo-document-picker.
3. src/hooks/useBook.ts — useBooks, useBookProfile, useUploadBook hooks with TanStack Query.
4. app/upload.tsx — upload screen with states: idle → picking → uploading → processing → processed/failed. Show progress bar, spinner, error retry.
5. app/books/index.tsx — book list with title, status badge, progress, current tidbit. FAB to upload. Pull-to-refresh. Empty state.

Use the theme tokens for styling. Make it mobile-friendly with large touch targets.
```
