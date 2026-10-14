# Integration Guide

## Add the Widget to Any Website

### Script-tag embed (HTML, WordPress, Shopify, Webflow, CMS sites)

Build the standalone bundle:

```bash
cd widget
npm install
npm run build
```

Upload `dist/ai-website-assistant.iife.js` to your CDN or static host, then add
the following immediately before `</body>`. The component uses Shadow DOM, so
its styles do not affect the host website.

```html
<script src="https://cdn.example.com/ai-website-assistant.iife.js" defer></script>
<ai-website-assistant
  api-url="https://api.example.com"
  title="Support Assistant"
  subtitle="Ask us anything"
  accent-color="#6366f1"
  position="bottom-right"
  suggested-prompts='["How do I get started?", "What are your prices?"]'>
</ai-website-assistant>
```

Supported attributes are `api-url` (required), `title`, `subtitle`, `theme`
(`light` or `dark`), `suggested-prompts` (a JSON string array), `position`, and
`accent-color`. Set `CORS_ORIGINS` on the backend to include the site origin.

### React integration

### 1. Copy the Widget

Copy the `widget/src/components/`, `widget/src/hooks/`, `widget/src/services/`, `widget/src/types/`, and `widget/src/styles/` directories into your project.

### 2. Install Dependencies

```bash
npm install react-markdown remark-gfm motion
```

### 3. Import the CSS

In your main entry file (e.g., `main.tsx` or `index.tsx`):

```tsx
import './path/to/widget/styles/index.css';
```

### 4. Add the Widget

```tsx
import { ChatWidget } from './path/to/widget/components/ChatWidget';

function App() {
  return (
    <div>
      {/* Your existing app content */}
      <YourExistingApp />

      {/* Add the chat widget */}
      <ChatWidget
        apiUrl="https://your-api-domain.com"
        title="Support Assistant"
        subtitle="Ask me anything"
        suggestedPrompts={[
          'How do I get started?',
          'What are your pricing plans?',
          'How do I contact support?',
        ]}
        position="bottom-right"
        accentColor="#6366f1"
      />
    </div>
  );
}
```

---

## Widget Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `apiUrl` | `string` | **required** | Backend API URL |
| `title` | `string` | `"AI Assistant"` | Widget header title |
| `subtitle` | `string` | `"Ask me anything..."` | Widget header subtitle |
| `theme` | `'light' \| 'dark'` | System preference | Initial theme |
| `suggestedPrompts` | `string[]` | Default prompts | Quick-start prompts |
| `position` | `'bottom-right' \| 'bottom-left'` | `'bottom-right'` | Button/window position |
| `accentColor` | `string` | `'#6366f1'` | Custom accent color |

---

## Customization

### Custom Accent Color

```tsx
<ChatWidget
  apiUrl="https://api.example.com"
  accentColor="#059669"  // Emerald green
/>
```

### Force Dark Mode

```tsx
<ChatWidget
  apiUrl="https://api.example.com"
  theme="dark"
/>
```

### Custom Suggested Prompts

```tsx
<ChatWidget
  apiUrl="https://api.example.com"
  suggestedPrompts={[
    'How does your product work?',
    'What integrations are available?',
    'Show me your API docs',
  ]}
/>
```

---

## Adding Website Knowledge

### Step 1: Add Documents

Place your website content files in the `backend/knowledge/` directory:

```
backend/knowledge/
├── features.md
├── pricing.md
├── faq.md
├── getting-started.md
├── api-docs.html
├── terms-of-service.txt
└── product-guide.pdf
```

### Step 2: Ingest

```bash
curl -X POST http://localhost:8000/ingest \
  -H "X-Admin-Key: your-admin-key"
```

`ADMIN_API_KEY` is required to enable ingestion. By default, documents can only
be read from `KNOWLEDGE_DIRECTORY`; set `ALLOW_CUSTOM_INGEST_DIRECTORY=true`
only when that is an intentional, trusted administrator capability.
Files above `MAX_INGEST_FILE_BYTES` (10 MB by default) are skipped, and a run
processes at most `MAX_INGEST_FILES` files.

### Step 3: Verify

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "pricing"}'
```

### Updating the Knowledge Base

To refresh with new documents:

```bash
# Add new files to knowledge/ directory, then:
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: your-admin-key" \
  -d '{"clear_existing": true}'
```

---

## Supported File Types

| Type | Extensions | Notes |
|------|-----------|-------|
| Markdown | `.md`, `.markdown` | Titles extracted from `# headings` |
| HTML | `.html`, `.htm` | Scripts, nav, footer stripped |
| PDF | `.pdf` | Per-page extraction |
| Word | `.docx` | Paragraphs + tables |
| JSON | `.json` | Recursive text extraction |
| Plain Text | `.txt` | Direct content |
