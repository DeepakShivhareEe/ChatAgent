/**
 * Demo application — shows the ChatWidget in action.
 * In production, users would import ChatWidget directly into their React app.
 */

import { ChatWidget } from './components/ChatWidget'

function App() {
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%)',
      fontFamily: "'Inter', sans-serif",
      color: '#e2e8f0',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '40px 20px',
    }}>
      {/* Demo page content */}
      <div style={{
        textAlign: 'center',
        maxWidth: '600px',
      }}>
        <div style={{
          fontSize: '48px',
          marginBottom: '16px',
        }}>
          🤖
        </div>
        <h1 style={{
          fontSize: '32px',
          fontWeight: 700,
          marginBottom: '12px',
          background: 'linear-gradient(135deg, #818cf8, #c084fc)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          letterSpacing: '-0.02em',
        }}>
          AI Website Assistant
        </h1>
        <p style={{
          fontSize: '16px',
          color: '#94a3b8',
          lineHeight: 1.7,
          marginBottom: '24px',
        }}>
          A production-ready AI chatbot platform with RAG pipeline, 
          multi-provider LLM support, and a beautiful chat widget.
        </p>
        <p style={{
          fontSize: '14px',
          color: '#64748b',
        }}>
          Click the chat button in the bottom right to try it out →
        </p>
      </div>

      {/* The AI Chat Widget */}
      <ChatWidget
        apiUrl={apiUrl}
        title="AI Assistant"
        subtitle="Ask me anything about the website"
        suggestedPrompts={[
          'What features do you offer?',
          'How does pricing work?',
          'How do I get started?',
          'How can I contact support?',
        ]}
        position="bottom-right"
      />
    </div>
  )
}

export default App
