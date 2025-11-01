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

  useEffect(() => {
    if (transcript && !isListening) {
      sendQuery(transcript);
    }
  }, [transcript, isListening, sendQuery]);

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
    if (isSpeaking) stopSpeaking();
  }, [resetTranscript, isSpeaking, stopSpeaking]);

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
            <div className="text-center text-gray-500 py-12">
              <Mic size={48} className="mx-auto mb-4 text-gray-600" />
              <p className="text-lg">Click the microphone to start talking</p>
              <p className="text-sm mt-2">Ask me anything!</p>
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
            <div className="bg-cyan-400/10 border border-cyan-400/30 rounded-xl p-3">
              <p className="text-cyan-400 text-sm">
                🎙️ {transcript}
              </p>
            </div>
          </div>
        )}

        {/* Controls */}
        <div className="p-4 border-t border-gray-700">
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

          <p className="text-xs text-gray-500 text-center mt-3">
            💡 Tip: Click microphone, speak your question, and get instant AI responses
          </p>
        </div>
      </div>
    </div>
  );
};

export default VoiceBotModal;
