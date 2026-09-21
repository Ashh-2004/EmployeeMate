import React, { useState, useEffect } from 'react';
import Sidebar, { DEFAULT_EMPLOYEES } from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import LoginModal from './components/LoginModal';
import { sendChatMessageStream, checkBackendHealth, fetchEmployees } from './services/api';

export default function App() {
  const [authData, setAuthData] = useState(null);
  const [employeesList, setEmployeesList] = useState(DEFAULT_EMPLOYEES);
  const [selectedEmp, setSelectedEmp] = useState(DEFAULT_EMPLOYEES[0]);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [serverOnline, setServerOnline] = useState(true);
  const [llmInfo, setLlmInfo] = useState({ provider: 'ollama', model: '' });

  useEffect(() => {
    verifyHealthAndEmployees();
    const interval = setInterval(verifyHealthAndEmployees, 10000);
    return () => clearInterval(interval);
  }, [authData]);

  const verifyHealthAndEmployees = async () => {
    const health = await checkBackendHealth();
    const isHealthy = typeof health === 'object' ? health.healthy : Boolean(health);
    setServerOnline(isHealthy);

    if (isHealthy && typeof health === 'object') {
      setLlmInfo({
        provider: health.llm_provider || 'ollama',
        model: health.llm_model || ''
      });
    }

    if (isHealthy && authData) {
      const liveData = await fetchEmployees();
      if (liveData && liveData.length > 0) {
        setEmployeesList(liveData);
        setSelectedEmp((prev) => {
          const match = liveData.find((e) => e.emp_id === (authData.emp_id || prev?.emp_id));
          return match ? match : liveData[0];
        });
      }
    }
  };

  const handleSendMessage = async (promptText) => {
    if (!promptText.trim() || !selectedEmp) return;

    setError(null);
    const userMsgId = Date.now().toString();
    const botMsgId = (Date.now() + 1).toString();

    const userMessage = {
      id: userMsgId,
      sender: 'user',
      text: promptText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    const historyToSend = messages;
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    // Create draft assistant message for real-time token streaming
    const botMessagePlaceholder = {
      id: botMsgId,
      sender: 'assistant',
      text: '',
      sources: [],
      tools_used: [],
      agent_routed: 'EmployeeMate',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, botMessagePlaceholder]);

    await sendChatMessageStream({
      prompt: promptText,
      empId: selectedEmp.emp_id,
      history: historyToSend,
      onMetadata: (metadata) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === botMsgId
              ? {
                  ...msg,
                  sources: metadata.sources || [],
                  tools_used: metadata.tools_used || [],
                  agent_routed: metadata.agent_routed || 'EmployeeMate'
                }
              : msg
          )
        );

        if (metadata.updated_employees) {
          setEmployeesList(metadata.updated_employees);
          const match = metadata.updated_employees.find((e) => e.emp_id === selectedEmp.emp_id);
          if (match) setSelectedEmp(match);
        }
      },
      onToken: (token) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === botMsgId
              ? { ...msg, text: msg.text + token }
              : msg
          )
        );
      },
      onError: (errMsg) => {
        setError(`Error from assistant: ${errMsg}`);
      }
    });

    setIsLoading(false);
  };

  const handleClearChat = () => {
    setMessages([]);
    setError(null);
  };

  if (!authData) {
    return <LoginModal onLoginSuccess={(data) => setAuthData(data)} />;
  }

  return (
    <div className="flex h-screen w-screen bg-[#fcf5eb] text-[#1c1e21] font-sans overflow-hidden">
      <Sidebar
        employees={employeesList}
        selectedEmp={selectedEmp}
        onSelectEmp={(emp) => {
          setSelectedEmp(emp);
          setError(null);
        }}
        onSendQuickPrompt={handleSendMessage}
        serverOnline={serverOnline}
        onRefreshHealth={verifyHealthAndEmployees}
        llmInfo={llmInfo}
      />

      <ChatWindow
        messages={messages}
        selectedEmp={selectedEmp}
        isLoading={isLoading}
        error={error}
        onSendMessage={handleSendMessage}
        onClearChat={handleClearChat}
        onSendQuickPrompt={handleSendMessage}
        llmInfo={llmInfo}
      />
    </div>
  );
}
