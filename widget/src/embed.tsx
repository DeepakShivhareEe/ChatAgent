/**
 * Framework-independent embed entry point.
 *
 * It registers <ai-website-assistant>, so any site that can load a modern
 * JavaScript file (including CMS and no-code sites) can use the widget.
 */
import { createRoot, type Root } from 'react-dom/client';
import { ChatWidget } from './components/ChatWidget';
import widgetStyles from './styles/index.css?inline';

const ATTRIBUTE_NAMES = [
  'api-url',
  'title',
  'subtitle',
  'theme',
  'suggested-prompts',
  'position',
  'accent-color',
] as const;

function promptsFromAttribute(value: string | null): string[] | undefined {
  if (!value) return undefined;

  try {
    const prompts: unknown = JSON.parse(value);
    return Array.isArray(prompts) && prompts.every((item) => typeof item === 'string')
      ? prompts
      : undefined;
  } catch {
    console.warn('[AI Website Assistant] suggested-prompts must be a JSON array of strings.');
    return undefined;
  }
}

class AIWebsiteAssistantElement extends HTMLElement {
  static get observedAttributes(): string[] {
    return [...ATTRIBUTE_NAMES];
  }

  private root: Root | null = null;
  private mountPoint: HTMLDivElement | null = null;

  connectedCallback(): void {
    if (this.root) return;

    const shadow = this.attachShadow({ mode: 'open' });
    const style = document.createElement('style');
    style.textContent = widgetStyles;
    this.mountPoint = document.createElement('div');
    shadow.append(style, this.mountPoint);
    this.root = createRoot(this.mountPoint);
    this.renderWidget();
  }

  disconnectedCallback(): void {
    this.root?.unmount();
    this.root = null;
    this.mountPoint = null;
  }

  attributeChangedCallback(): void {
    this.renderWidget();
  }

  private renderWidget(): void {
    if (!this.root) return;

    const apiUrl = this.getAttribute('api-url');
    if (!apiUrl) {
      console.error('[AI Website Assistant] The api-url attribute is required.');
      return;
    }

    const theme = this.getAttribute('theme');
    const position = this.getAttribute('position');
    this.root.render(
      <ChatWidget
        key={apiUrl}
        apiUrl={apiUrl}
        title={this.getAttribute('title') || undefined}
        subtitle={this.getAttribute('subtitle') || undefined}
        theme={theme === 'light' || theme === 'dark' ? theme : undefined}
        suggestedPrompts={promptsFromAttribute(this.getAttribute('suggested-prompts'))}
        position={position === 'bottom-left' || position === 'bottom-right' ? position : undefined}
        accentColor={this.getAttribute('accent-color') || undefined}
      />,
    );
  }
}

if (!customElements.get('ai-website-assistant')) {
  customElements.define('ai-website-assistant', AIWebsiteAssistantElement);
}

export { AIWebsiteAssistantElement };
