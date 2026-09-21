import React from 'react';
import { Bot, User, Wrench, FileText, Cpu, Check, Copy, CheckCheck } from 'lucide-react';

function parseMarkdown(text) {
  if (!text) return null;

  const parseInline = (content) => {
    if (typeof content !== 'string') return content;
    const tokens = [];
    // Matches **bold**, *italic*, `code`
    const inlineRegex = /(\*\*(.*?)\*\*|\*(.*?)\*|`(.*?)`)/g;
    let lastIndex = 0;
    let match;

    while ((match = inlineRegex.exec(content)) !== null) {
      if (match.index > lastIndex) {
        tokens.push(content.substring(lastIndex, match.index));
      }
      if (match[2] !== undefined) {
        tokens.push(<strong key={match.index} className="font-bold">{parseInline(match[2])}</strong>);
      } else if (match[3] !== undefined) {
        tokens.push(<em key={match.index} className="italic">{match[3]}</em>);
      } else if (match[4] !== undefined) {
        tokens.push(
          <code key={match.index} className="bg-[#f0f4f9] text-[#1c1e21] px-1.5 py-0.5 rounded font-mono text-[12px] border border-[#d8c7b5]/40">
            {match[4]}
          </code>
        );
      }
      lastIndex = inlineRegex.lastIndex;
    }

    if (lastIndex < content.length) {
      tokens.push(content.substring(lastIndex));
    }

    return tokens.length > 0 ? tokens : content;
  };

  const lines = text.split('\n');
  const elements = [];
  let numberedCount = 0;

  lines.forEach((line, lineIdx) => {
    const trimmed = line.trim();

    if (trimmed.startsWith('### ')) {
      numberedCount = 0;
      elements.push(<h3 key={lineIdx} className="font-bold text-base mt-2 mb-1">{parseInline(trimmed.slice(4))}</h3>);
    } else if (trimmed.startsWith('## ')) {
      numberedCount = 0;
      elements.push(<h2 key={lineIdx} className="font-bold text-lg mt-2 mb-1">{parseInline(trimmed.slice(3))}</h2>);
    } else if (trimmed.startsWith('# ')) {
      numberedCount = 0;
      elements.push(<h1 key={lineIdx} className="font-bold text-xl mt-2 mb-1">{parseInline(trimmed.slice(2))}</h1>);
    } else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      const itemContent = trimmed.slice(2);
      elements.push(
        <div key={lineIdx} className="flex items-start space-x-2 my-1 pl-1">
          <span className="text-[#25d366] font-bold text-sm leading-tight select-none">•</span>
          <div className="flex-1 leading-relaxed">{parseInline(itemContent)}</div>
        </div>
      );
    } else if (/^\d+\.\s/.test(trimmed)) {
      numberedCount += 1;
      const match = trimmed.match(/^\d+\.\s/);
      const prefixLen = match ? match[0].length : 3;
      const itemContent = trimmed.slice(prefixLen);
      elements.push(
        <div key={lineIdx} className="flex items-start space-x-2 my-1.5 pl-0.5">
          <span className="font-bold text-[#111b21] bg-[#25d366]/15 px-1.5 py-0.5 rounded text-xs font-mono border border-[#25d366]/30 flex-shrink-0 mt-0.5">
            {numberedCount}.
          </span>
          <div className="flex-1 leading-relaxed">{parseInline(itemContent)}</div>
        </div>
      );
    } else if (trimmed === '') {
      elements.push(<div key={lineIdx} className="h-1.5" />);
    } else {
      numberedCount = 0;
      elements.push(
        <p key={lineIdx} className="my-0.5 leading-relaxed">
          {parseInline(line)}
        </p>
      );
    }
  });

  return elements;
}

export default function MessageBubble({ message, currentUser }) {
  const [copied, setCopied] = React.useState(false);
  const isUser = message.sender === 'user';

  const handleCopy = () => {
    navigator.clipboard.writeText(message.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Helper for agent badge styling
  const getAgentBadgeStyle = (agentName) => {
    switch (agentName) {
      case 'KnowledgeAgent':
        return {
          label: 'Knowledge Agent (RAG)',
          className: 'bg-[#0373e9]/10 text-[#0373e9] border-[#0373e9]/30'
        };
      case 'HRAgent':
        return {
          label: 'HR Specialist Agent',
          className: 'bg-[#25d366]/15 text-[#111b21] border-[#25d366]/30'
        };
      case 'Orchestrator_MultiAgent':
        return {
          label: 'Multi-Agent Orchestrator',
          className: 'bg-purple-100 text-purple-800 border-purple-200'
        };
      default:
        return {
          label: agentName || 'System Agent',
          className: 'bg-[#f0f4f9] text-[#1c1e21] border-[#d8c7b5]'
        };
    }
  };

  return (
    <div className={`flex items-start space-x-3 my-3 max-w-4xl ${isUser ? 'ml-auto flex-row-reverse space-x-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs flex-shrink-0 shadow-sm ${
        isUser
          ? 'bg-[#25d366] text-white'
          : 'bg-white border border-[#f0f4f9] text-[#1c1e21]'
      }`}>
        {isUser ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-[#25d366]" />}
      </div>

      {/* Bubble Box */}
      <div className={`flex flex-col space-y-1.5 max-w-[85%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`p-4 rounded-[12px] text-sm leading-relaxed relative group shadow-sm border break-words ${
          isUser
            ? 'bg-[#d9fdd3] text-[#111b21] border-[#bbf2b3] bubble-outgoing'
            : 'bg-white text-[#1c1e21] border-[#f0f4f9] bubble-incoming'
        }`}>
          {/* Main Message Text */}
          <div className="break-words font-sans">
            {message.text && message.text.trim() ? (
              parseMarkdown(message.text)
            ) : (
              <span className="text-[#5e5e5e] italic text-xs"></span>
            )}
          </div>

          {/* Copy Button */}
          {!isUser && (
            <button
              onClick={handleCopy}
              className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 p-1.5 rounded-full bg-[#f0f4f9] hover:bg-[#e4ebf3] text-[#5e5e5e] hover:text-[#1c1e21] transition-all"
              title="Copy answer"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-[#25d366]" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          )}

          {/* Timestamp inline footer */}
          <div className={`flex items-center justify-end space-x-1 text-[11px] text-[#5e5e5e] mt-1 pt-1 ${isUser ? 'border-t border-[#bbf2b3]/50' : 'border-t border-[#f0f4f9]'}`}>
            <span>{message.timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
            {isUser && <CheckCheck className="w-3.5 h-3.5 text-[#25d366] inline" />}
          </div>
        </div>

        {/* Assistant Rich Metadata Badges */}
        {!isUser && (message.agent_routed || (message.tools_used && message.tools_used.length > 0) || (message.sources && message.sources.length > 0)) && (
          <div className="flex flex-wrap gap-2 pt-0.5 text-xs">
            {/* 1. Agent Routing Badge */}
            {message.agent_routed && (
              <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-[50px] border font-medium ${getAgentBadgeStyle(message.agent_routed).className}`}>
                <Cpu className="w-3 h-3" />
                Routed via: {getAgentBadgeStyle(message.agent_routed).label}
              </span>
            )}

            {/* 2. Tool Execution Badges */}
            {message.tools_used && message.tools_used.map((tool, idx) => (
              <span key={idx} className="inline-flex items-center gap-1 px-3 py-1 rounded-[50px] bg-amber-50 text-amber-800 border border-amber-200 font-medium">
                <Wrench className="w-3 h-3 text-amber-600" />
                Executed: <code className="font-mono text-[11px]">{tool}</code>
              </span>
            ))}

            {/* 3. Document Sources Badges */}
            {message.sources && message.sources.map((src, idx) => (
              <span key={idx} className="inline-flex items-center gap-1 px-3 py-1 rounded-[50px] bg-[#0373e9]/10 text-[#0373e9] border border-[#0373e9]/20 font-medium">
                <FileText className="w-3 h-3" />
                Source: <span className="font-mono text-[11px]">{src}</span>
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
