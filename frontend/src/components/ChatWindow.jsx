import React, { useRef, useEffect, useState } from 'react';
import MessageBubble from './MessageBubble';
import { Send, Trash2, Bot, Sparkles, AlertCircle, Loader2, Compass, ArrowRight, Download, MessageSquare } from 'lucide-react';

export default function ChatWindow({
  messages,
  selectedEmp,
  isLoading,
  error,
  onSendMessage,
  onClearChat,
  onSendQuickPrompt,
  llmInfo
}) {
  const [inputPrompt, setInputPrompt] = useState('');
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom on new messages or loading state update
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputPrompt.trim() || isLoading) return;
    onSendMessage(inputPrompt);
    setInputPrompt('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const provider = (llmInfo?.provider || 'ollama').toLowerCase();
  let llmBadgeColor = 'bg-blue-50 text-blue-700 border-blue-200';
  let llmIcon = '🖥️';
  let llmLabel = 'Local (Ollama)';

  if (provider === 'gemini') {
    llmBadgeColor = 'bg-purple-50 text-purple-700 border-purple-200';
    llmIcon = '✦';
    llmLabel = 'Gemini';
  } else if (provider === 'openai') {
    llmBadgeColor = 'bg-emerald-50 text-emerald-700 border-emerald-200';
    llmIcon = '⚡';
    llmLabel = 'OpenAI';
  } else if (provider === 'lmstudio' || provider === 'local') {
    llmBadgeColor = 'bg-amber-50 text-amber-700 border-amber-200';
    llmIcon = '💻';
    llmLabel = 'Local (LM Studio)';
  }

  return (
    <div className="flex-1 flex flex-col h-full bg-[#fcf5eb] relative overflow-hidden">
      {/* Top Navigation / Status Header */}
      <header className="h-14 border-b border-[#f0f4f9] bg-[#ffffff] px-5 flex items-center justify-between flex-shrink-0 z-10">
        <div className="flex items-center space-x-2.5">
          <div className="w-2 h-2 rounded-full bg-[#25d366] animate-pulse" />
          <div>
            <h2 className="text-xs font-bold text-[#1c1e21] flex items-center gap-2">
              EmployeeMate HR Assistant
              {selectedEmp?.emp_id && (
                <span className="text-[10px] bg-[#f0f4f9] text-[#1c1e21] px-2 py-0.5 rounded-full font-mono border border-[#d8c7b5]/40">
                  {selectedEmp.emp_id}
                </span>
              )}
            </h2>
            <p className="text-[10px] text-[#5e5e5e]">Context: {selectedEmp?.name} ({selectedEmp?.role})</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Active LLM Provider Pill */}
          <div className={`px-2.5 py-1 rounded-full text-[10px] font-semibold border flex items-center gap-1.5 ${llmBadgeColor}`}>
            <span>{llmIcon}</span>
            <span>LLM: <strong>{llmLabel}</strong></span>
            {llmInfo?.model && (
              <span className="text-[9px] opacity-75 font-mono">({llmInfo.model})</span>
            )}
          </div>

          {messages.length > 0 && (
            <button
              onClick={onClearChat}
              className="flex items-center space-x-1 px-3 py-1.5 rounded-full text-[11px] font-semibold text-[#1c1e21] bg-transparent border border-[#1c1e21] hover:bg-[#1c1e21] hover:text-white transition-all"
              title="Clear Conversation"
            >
              <Trash2 className="w-3 h-3" />
              <span>Clear Chat</span>
            </button>
          )}
        </div>
      </header>

      {/* Main Conversational Container */}
      <main className="flex-1 overflow-y-auto p-5 space-y-3">
        {messages.length === 0 ? (
          /* Empty State Welcome Screen */
          <div className="h-full flex flex-col items-center justify-center text-center max-w-xl mx-auto p-4 space-y-6 my-auto">
            {/* Floating Chat Bubbles Decor */}
            <div className="w-full space-y-2.5 max-w-md mx-auto text-left">
              <div className="bg-white p-3 rounded-xl bubble-incoming shadow-sm border border-[#f0f4f9] text-[11px] text-[#1c1e21] max-w-[260px] ml-0">
                Hello {selectedEmp?.shortName || selectedEmp?.name?.split(' ')[0]}! I am HR, your EmployeeMate assistant. How can I help today?
                <div className="text-[9px] text-[#5e5e5e] text-right mt-1">09:41 AM</div>
              </div>
              <div className="bg-[#d9fdd3] p-3 rounded-xl bubble-outgoing shadow-sm text-[11px] text-[#111b21] max-w-[260px] ml-auto">
                What is our remote work policy & how many leave days do I have?
                <div className="text-[9px] text-[#5e5e5e] text-right mt-1">09:42 AM ✓✓</div>
              </div>
            </div>

            {/* Display Typography */}
            <div className="space-y-2">
              <h1 className="text-3xl md:text-4xl font-extrabold text-[#1c1e21] tracking-tight leading-[1.1]">
                Welcome to <span className="text-[#25d366]">EmployeeMate</span>
              </h1>
              <p className="text-sm text-[#5e5e5e] max-w-sm mx-auto leading-snug">
                Your AI HR Assistant
              </p>
              <p className="text-xs text-[#5e5e5e] max-w-sm mx-auto leading-snug">
                Ask policy questions, check leave balances, or request time off.
              </p>
            </div>

            {/* Interactive Suggestion Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-lg">
              <button
                onClick={() => onSendQuickPrompt("What is the WFH policy for remote work?")}
                className="p-3.5 text-left rounded-xl bg-white border border-[#f0f4f9] hover:border-[#0373e9]/50 hover:bg-white transition-all text-[11px] space-y-1 group shadow-sm"
              >
                <div className="font-semibold text-[#1c1e21] group-hover:text-[#0373e9] flex items-center gap-1.5">
                  <Compass className="w-3.5 h-3.5 text-[#0373e9]" /> WFH Policy
                </div>
                <div className="text-[#5e5e5e] text-[11px] truncate">Core hours & remote days</div>
                <div className="text-[#0373e9] font-semibold flex items-center gap-1 text-[10px] pt-0.5">
                  Learn more <ArrowRight className="w-2.5 h-2.5 group-hover:translate-x-1 transition-transform" />
                </div>
              </button>

              <button
                onClick={() => onSendQuickPrompt(`Apply 2 days leave for ${selectedEmp?.emp_id || 'EMP001'} from 2026-10-15 to 2026-10-16 reason: Personal`)}
                className="p-3.5 text-left rounded-xl bg-white border border-[#f0f4f9] hover:border-[#25d366]/50 hover:bg-white transition-all text-[11px] space-y-1 group shadow-sm"
              >
                <div className="font-semibold text-[#1c1e21] group-hover:text-[#25d366] flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-[#25d366]" /> Apply Leave
                </div>
                <div className="text-[#5e5e5e] text-[11px] truncate">Book leave with balance check</div>
                <div className="text-[#25d366] font-semibold flex items-center gap-1 text-[10px] pt-0.5">
                  Submit request <ArrowRight className="w-2.5 h-2.5 group-hover:translate-x-1 transition-transform" />
                </div>
              </button>

              <button
                onClick={() => onSendQuickPrompt("What is the travel reimbursement policy?")}
                className="p-3.5 text-left rounded-xl bg-white border border-[#f0f4f9] hover:border-[#0373e9]/50 hover:bg-white transition-all text-[11px] space-y-1 group shadow-sm"
              >
                <div className="font-semibold text-[#1c1e21] group-hover:text-[#0373e9] flex items-center gap-1.5">
                  <Compass className="w-3.5 h-3.5 text-[#0373e9]" /> Travel Policy
                </div>
                <div className="text-[#5e5e5e] text-[11px] truncate">Per diem & reimbursement rules</div>
                <div className="text-[#0373e9] font-semibold flex items-center gap-1 text-[10px] pt-0.5">
                  Learn more <ArrowRight className="w-2.5 h-2.5 group-hover:translate-x-1 transition-transform" />
                </div>
              </button>

              <button
                onClick={() => onSendQuickPrompt("What are the IT security guidelines?")}
                className="p-3.5 text-left rounded-xl bg-white border border-[#f0f4f9] hover:border-[#0373e9]/50 hover:bg-white transition-all text-[11px] space-y-1 group shadow-sm"
              >
                <div className="font-semibold text-[#1c1e21] group-hover:text-[#0373e9] flex items-center gap-1.5">
                  <Compass className="w-3.5 h-3.5 text-[#0373e9]" /> IT Security
                </div>
                <div className="text-[#5e5e5e] text-[11px] truncate">Password & VPN guidelines</div>
                <div className="text-[#0373e9] font-semibold flex items-center gap-1 text-[10px] pt-0.5">
                  Learn more <ArrowRight className="w-2.5 h-2.5 group-hover:translate-x-1 transition-transform" />
                </div>
              </button>
            </div>
          </div>
        ) : (
          /* Render Messages */
          messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} currentUser={selectedEmp} />
          ))
        )}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex items-center space-x-2.5 my-3 max-w-md">
            <div className="w-8 h-8 rounded-full bg-white border border-[#f0f4f9] flex items-center justify-center text-[#25d366] flex-shrink-0 shadow-sm">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-[#25d366]" />
            </div>
            <div className="p-3 rounded-xl bubble-incoming bg-white border border-[#f0f4f9] text-[11px] text-[#1c1e21] flex items-center gap-2 shadow-sm">
              <span className="w-1.5 h-1.5 rounded-full bg-[#25d366] animate-ping" />
              Routing query & executing agent tools...
            </div>
          </div>
        )}

        {/* Error Notification */}
        {error && (
          <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-[11px] flex items-center gap-2 my-2 shadow-sm">
            <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 text-rose-600" />
            <span>{error}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </main>

      {/* Input Form Bar */}
      <footer className="p-3 border-t border-[#f0f4f9] bg-white flex-shrink-0">
        <form onSubmit={handleSubmit} className="relative max-w-4xl mx-auto flex items-center">
          <input
            type="text"
            value={inputPrompt}
            onChange={(e) => setInputPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={`Type a message as ${selectedEmp?.name || 'Employee'} (${selectedEmp?.emp_id || 'EMP001'})...`}
            disabled={isLoading}
            className="w-full bg-[#f0f4f9] border border-transparent text-[#1c1e21] placeholder-[#5e5e5e] text-xs rounded-full pl-4 pr-12 py-3 focus:outline-none focus:bg-white focus:border-[#25d366] transition-all disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!inputPrompt.trim() || isLoading}
            className="absolute right-1.5 p-2 rounded-full bg-[#25d366] hover:bg-[#20bd5a] text-white disabled:opacity-40 transition-all flex items-center justify-center"
            title="Send Prompt"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </form>
        <div className="text-[10px] text-[#5e5e5e] text-center mt-1.5">
          Press <kbd className="px-1 py-0.5 bg-[#f0f4f9] text-[#1c1e21] rounded border border-[#d8c7b5]/50 font-mono text-[9px]">Enter</kbd> to ask EmployeeMate
        </div>
      </footer>
    </div>
  );
}
