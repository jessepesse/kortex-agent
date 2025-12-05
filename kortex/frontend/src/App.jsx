import React, { useState, useEffect } from 'react';
import Chat from './components/Chat';
import Sidebar from './components/Sidebar';
import FunctionCallModal from './components/FunctionCallModal';
import SettingsModal from './components/SettingsModal';
import * as api from './services/api';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [contextData, setContextData] = useState({
    energy: 75,
    location: 'Unknown',
    focus: 'Loading...'
  });

  const [pendingFunctionCalls, setPendingFunctionCalls] = useState(null);
  const [councilLoading, setCouncilLoading] = useState(null); // 'hive' or 'elite' when loading

  // Load context data periodically
  useEffect(() => {
    loadContextData();
    const contextInterval = setInterval(() => {
      loadContextData();
    }, 10000); // Refresh context every 10 seconds

    // Listen for chat updates to refresh context
    const handleChatUpdate = () => {
      loadContextData();
    };
    window.addEventListener('chatHistoryChanged', handleChatUpdate);

    return () => {
      clearInterval(contextInterval);
      window.removeEventListener('chatHistoryChanged', handleChatUpdate);
    };
  }, []);

  const loadContextData = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:5001'}/api/data/health`);
      const healthResponse = await response.json();
      const healthData = healthResponse.data || healthResponse;

      const profileResponse = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:5001'}/api/data/profile`);
      const profileResponseData = await profileResponse.json();
      const profileData = profileResponseData.data || profileResponseData;

      setContextData({
        energy: healthData.current_state?.energy || 75,
        location: profileData.current_location || 'Unknown',
        focus: profileData.current_focus || 'General'
      });
    } catch (error) {
      console.error('Failed to load context data:', error);
    }
  };

  const handleSendMessage = async (text, files = []) => {
    // Add user message immediately
    const userMessage = { role: 'user', content: text, timestamp: new Date().toISOString() };
    if (files.length > 0) {
      userMessage.files = files.map(f => ({ name: f.name, type: f.type }));
    }
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      let response;

      // Check for commands
      if (text.startsWith('/council') || text.startsWith('/elite')) {
        const query = text.replace(/^\/(council|elite)/, '').trim();
        setCouncilLoading('elite');
        response = await api.runCouncil(query, messages);

        // Elite Council response handling
        const councilMessage = {
          role: 'assistant',
          type: 'council',
          councilType: 'elite',
          content: response.chairman_response,
          councilData: response,
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, councilMessage]);
        setCouncilLoading(null);

      } else if (text.startsWith('/hive')) {
        const query = text.replace('/hive', '').trim();
        setCouncilLoading('hive');
        response = await api.runHive(query, messages);

        // Hive Council response handling
        const hiveMessage = {
          role: 'assistant',
          type: 'council',
          councilType: 'hive',
          content: response.chairman_response,
          councilData: response,
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, hiveMessage]);
        setCouncilLoading(null);

      } else if (text.startsWith('/mega')) {
        const query = text.replace('/mega', '').trim();
        setCouncilLoading('mega');
        response = await api.runMega(query, messages);

        // Mega Council response handling
        const megaMessage = {
          role: 'assistant',
          type: 'council',
          councilType: 'mega',
          content: response.mega_verdict,
          councilData: response,
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, megaMessage]);
        setCouncilLoading(null);

      } else {
        // Standard chat (with optional files)
        response = await api.sendMessage(text, messages, null, null, currentChatId, files);

        if (response.chat_id && !currentChatId) {
          setCurrentChatId(response.chat_id);
        }

        // Handle function calls if any
        if (response.function_calls) {
          setPendingFunctionCalls(response.function_calls);
        }

        // Handle text response if present (even if there are function calls)
        if (response.response || response.error) {
          let content = response.response || response.error;

          // Append Scribe updates if any
          if (response.scribe_updates && response.scribe_updates.length > 0) {
            content += "\n\n" + response.scribe_updates.map(u => `📝 *System Update:* ${u}`).join("\n");
          }

          const aiMessage = {
            role: 'assistant',
            content: content,
            timestamp: new Date().toISOString()
          };
          setMessages(prev => [...prev, aiMessage]);

          // Notify sidebar that chat history has changed
          window.dispatchEvent(new CustomEvent('chatHistoryChanged'));
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request.',
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setCurrentChatId(null);
    if (window.innerWidth < 768) {
      setIsSidebarOpen(false);
    }
  };

  const handleSelectChat = async (chatId) => {
    try {
      setIsLoading(true);
      const chat = await api.getChat(chatId);
      if (chat && chat.messages) {
        setMessages(chat.messages);
        setCurrentChatId(chat.id);
      }
      if (window.innerWidth < 768) {
        setIsSidebarOpen(false);
      }
    } catch (error) {
      console.error('Failed to load chat:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApproveFunctionCalls = async () => {
    if (!pendingFunctionCalls) return;

    try {
      // Execute all function calls
      const results = [];
      for (const fc of pendingFunctionCalls) {
        const result = await api.executeFunction(fc.name, fc.args);
        results.push(result);
      }

      // Show success message
      const successMessage = results.map(r => r.message).join('\n');
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `✓ ${successMessage}`,
        timestamp: new Date().toISOString()
      }]);

      setPendingFunctionCalls(null);
    } catch (error) {
      console.error('Failed to execute function calls:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `❌ Error executing updates: ${error.message}`,
        timestamp: new Date().toISOString()
      }]);
      setPendingFunctionCalls(null);
    }
  };

  const handleRejectFunctionCalls = () => {
    setMessages(prev => [...prev, {
      role: 'assistant',
      content: '✗ Updates cancelled by user.',
      timestamp: new Date().toISOString()
    }]);
    setPendingFunctionCalls(null);
  };

  return (
    <div className="app-container">
      <Sidebar
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        onNewChat={handleNewChat}
        onSelectChat={handleSelectChat}
        onOpenSettings={() => setShowSettings(true)}
        contextData={contextData}
      />

      <main className={`main-content ${isSidebarOpen ? 'sidebar-open' : ''}`}>
        <Chat
          messages={messages}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          isSidebarOpen={isSidebarOpen}
          contextData={contextData}
          councilLoading={councilLoading}
        />
      </main>

      <FunctionCallModal
        functionCalls={pendingFunctionCalls}
        onApprove={handleApproveFunctionCalls}
        onReject={handleRejectFunctionCalls}
      />

      <SettingsModal
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
      />
    </div>
  );
}

export default App;
