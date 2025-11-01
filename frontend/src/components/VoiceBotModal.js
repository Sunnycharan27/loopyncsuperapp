import React, { useState, useCallback, useEffect } from 'react';
import axios from 'axios';
import { Mic, MicOff, Send, Volume2, VolumeX, X } from 'lucide-react';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';
import { useTextToSpeech } from '../hooks/useTextToSpeech';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const VoiceBotModal = ({ isOpen, onClose }) => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sessionId] = useState(() => 
    `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  );
  const [textInput, setTextInput] = useState('');
  const [isMobile, setIsMobile] = useState(false);

  const {
    transcript,
    isListening,
    browserSupportsSpeech,
    error: speechError,
    startListening,
    stopListening,
    resetTranscript
  } = useSpeechRecognition();

  const {
    isSpeaking,
    speak,
    stop: stopSpeaking
  } = useTextToSpeech();

  // Detect mobile device
  useEffect(() => {
    const checkMobile = () => {
      const userAgent = navigator.userAgent || navigator.vendor || window.opera;
      const mobile = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent.toLowerCase());
      setIsMobile(mobile);
    };
    checkMobile();
  }, []);

  const sendQuery = useCallback(async (query) => {
    if (!query.trim()) return;

    try {
      setError(null);
      setIsLoading(true);

      console.log('Sending query to AI:', query);

      // Add user message
      setMessages(prev => [...prev, {
        role: 'user',
        content: query,
        timestamp: new Date()
      }]);

      const response = await axios.post(`${API_URL}/api/voice/chat`, {
        query,
        session_id: sessionId,
        temperature: 0.7,
        max_tokens: 512
      }, {
        timeout: 30000
      });

      console.log('AI Response:', response.data);

      if (response.data.success) {
        const botMessage = {
          role: 'assistant',
          content: response.data.data.response,
          timestamp: new Date()
        };

        setMessages(prev => [...prev, botMessage]);

        // Speak the response using text-to-speech
        console.log('Speaking AI response:', response.data.data.response);
        speak(response.data.data.response);
      } else {
        throw new Error('AI response was not successful');
      }

      resetTranscript();
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Unknown error';
      setError(errorMessage);
      console.error('Error sending query:', err);
      
      // Add error message to chat
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Sorry, I encountered an error: ${errorMessage}`,
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, resetTranscript, speak]);

  // Add welcome message when modal opens
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      const welcomeMessage = {
        role: 'assistant',
        content: "Hi! I'm your AI voice assistant. Click the microphone button and ask me anything!",
        timestamp: new Date()
      };
      setMessages([welcomeMessage]);
      
      // Speak welcome message
      setTimeout(() => {
        speak("Hi! I'm your AI voice assistant. Click the microphone button and ask me anything!");
      }, 500);
    }
  }, [isOpen, messages.length, speak]);

  // Send query when transcript is ready
  useEffect(() => {
    if (transcript && !isListening) {
      sendQuery(transcript);
    }
  }, [transcript, isListening, sendQuery]);

  const handleVoiceInput = useCallback(() => {
    if (isListening) {
      stopListening();
    } else {
      resetTranscript();
      startListening();
    }
  }, [isListening, startListening, stopListening, resetTranscript]);

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
    resetTranscript();
    setTextInput('');
    if (isSpeaking) stopSpeaking();
  }, [resetTranscript, isSpeaking, stopSpeaking]);

  const handleTextSubmit = useCallback((e) => {
    e?.preventDefault();
    if (textInput.trim()) {
      sendQuery(textInput);
      setTextInput('');
    }
  }, [textInput, sendQuery]);

  if (!isOpen) return null;

  if (!browserSupportsSpeech) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
        <div className="bg-gray-900 rounded-2xl p-6 max-w-md mx-4 border border-red-500/50">
          <h3 className="text-white text-xl font-bold mb-4">⚠️ Browser Not Supported</h3>
          <p className="text-gray-300 mb-4">
            Speech Recognition is not supported in your browser. Please use Chrome, Edge, or Safari for voice bot functionality.
          </p>
          <button 
            onClick={onClose}
            className="w-full px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-xl font-semibold transition-all"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl w-full max-w-2xl max-h-[80vh] flex flex-col border border-cyan-400/30 shadow-2xl shadow-cyan-400/20">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Mic size={24} className="text-cyan-400" />
              AI Voice Assistant
            </h2>
            <p className="text-sm text-gray-400">Powered by OpenAI GPT-4o</p>
          </div>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded-lg transition-all"
          >
            <X size={24} className="text-gray-400 hover:text-white" />
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-gray-400 py-12">
              <Mic size={64} className="mx-auto mb-4 text-cyan-400/50" />
              <p className="text-xl font-semibold text-white mb-2">Welcome to AI Voice Assistant</p>
              <p className="text-sm mb-4">
                {isMobile ? 'Type your questions below' : 'Click the microphone button below and start talking'}
              </p>
              <div className="bg-gray-800/50 rounded-xl p-4 max-w-md mx-auto text-left">
                <p className="text-xs text-gray-400 mb-2">💡 Try asking:</p>
                <ul className="text-xs text-gray-500 space-y-1">
                  <li>• "What is Loopync?"</li>
                  <li>• "How do I add friends?"</li>
                  <li>• "Tell me about the features"</li>
                  <li>• "What can I do here?"</li>
                </ul>
              </div>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-2xl p-4 ${
                msg.role === 'user' 
                  ? 'bg-gradient-to-r from-cyan-400 to-blue-500 text-black' 
                  : 'bg-gray-800 text-white border border-gray-700'
              }`}>
                <p className="text-sm">{msg.content}</p>
                <p className={`text-xs mt-1 ${msg.role === 'user' ? 'text-black/60' : 'text-gray-500'}`}>
                  {msg.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-800 border border-gray-700 rounded-2xl p-4">
                <div className="flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-cyan-400 border-t-transparent"></div>
                  <p className="text-gray-400 text-sm">Thinking...</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Error Display */}
        {(error || speechError) && (
          <div className="px-4 pb-2">
            <div className="bg-red-500/20 border border-red-500/50 rounded-xl p-4">
              <p className="text-red-400 text-sm font-semibold mb-2">
                ⚠️ Error
              </p>
              <p className="text-red-300 text-sm">
                {error || speechError}
              </p>
              {(speechError && speechError.includes('denied')) && (
                <p className="text-red-200 text-xs mt-2">
                  💡 Tip: Click the 🔒 icon in your browser's address bar to allow microphone access
                </p>
              )}
            </div>
          </div>
        )}

        {/* AI Speaking Indicator */}
        {isSpeaking && (
          <div className="px-4 pb-2">
            <div className="bg-cyan-400/20 border border-cyan-400/50 rounded-xl p-3 flex items-center gap-2">
              <Volume2 size={18} className="text-cyan-400 animate-pulse" />
              <p className="text-cyan-400 text-sm font-semibold">
                AI is speaking...
              </p>
            </div>
          </div>
        )}

        {/* Transcript Display */}
        {transcript && (
          <div className="px-4 pb-2">
            <div className="bg-purple-400/10 border border-purple-400/30 rounded-xl p-3">
              <p className="text-purple-400 text-xs font-semibold mb-1">
                🎙️ You said:
              </p>
              <p className="text-white text-sm">
                {transcript}
              </p>
            </div>
          </div>
        )}

        {/* Controls */}
        <div className="p-4 border-t border-gray-700">
          {/* Show text input on mobile or when speech not supported */}
          {(isMobile || !browserSupportsSpeech || speechError) && (
            <form onSubmit={handleTextSubmit} className="mb-3">
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  placeholder="Type your message here..."
                  className="flex-1 px-4 py-3 bg-gray-800 text-white rounded-xl border border-gray-600 focus:border-cyan-400 focus:outline-none"
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  disabled={isLoading || !textInput.trim()}
                  className="px-4 py-3 bg-gradient-to-r from-cyan-400 to-blue-500 hover:from-cyan-500 hover:to-blue-600 text-black rounded-xl font-semibold transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Send size={20} />
                </button>
              </div>
            </form>
          )}

          {/* Voice controls - hide on mobile if speech not supported */}
          {(!isMobile || browserSupportsSpeech) && !speechError && (
            <div className="flex items-center gap-3">
              <button
                onClick={handleVoiceInput}
                disabled={isLoading}
                className={`flex-1 py-3 px-6 rounded-xl font-semibold transition-all flex items-center justify-center gap-2 ${
                  isListening
                    ? 'bg-red-500 hover:bg-red-600 text-white animate-pulse'
                    : 'bg-gradient-to-r from-cyan-400 to-blue-500 hover:from-cyan-500 hover:to-blue-600 text-black'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {isListening ? (
                  <>
                    <MicOff size={20} />
                    Listening...
                  </>
                ) : (
                  <>
                    <Mic size={20} />
                    Start Speaking
                  </>
                )}
              </button>

              {isSpeaking && (
                <button
                  onClick={stopSpeaking}
                  className="px-4 py-3 bg-orange-500 hover:bg-orange-600 text-white rounded-xl font-semibold transition-all flex items-center gap-2"
                >
                  <VolumeX size={20} />
                  Stop
                </button>
              )}

              <button
                onClick={clearChat}
                className="px-4 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-xl font-semibold transition-all"
              >
                Clear
              </button>
            </div>
          )}

          {/* Mobile-specific message */}
          {isMobile && (
            <p className="text-xs text-gray-500 text-center mt-3">
              📱 Mobile mode: Type your questions or try voice input above
            </p>
          )}

          {/* Desktop tip */}
          {!isMobile && browserSupportsSpeech && !speechError && (
            <p className="text-xs text-gray-500 text-center mt-3">
              💡 Tip: Click microphone, speak your question, and get instant AI responses
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default VoiceBotModal;
