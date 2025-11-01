import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  Search, Send, Phone, Video, Image, Smile, MoreVertical,
  ArrowLeft, Check, CheckCheck, Circle, Mic, X, Sparkles
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { useWebSocket } from '../context/WebSocketContext';
import CallManager from '../components/CallManager';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const MessengerNew = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { socket } = useWebSocket();
  
  const [currentUser, setCurrentUser] = useState(null);
  const [threads, setThreads] = useState([]);
  const [selectedThread, setSelectedThread] = useState(null);
  const [messages, setMessages] = useState([]);
  const [messageText, setMessageText] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [otherUserTyping, setOtherUserTyping] = useState(false);
  const [showAI, setShowAI] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  
  const messagesEndRef = useRef(null);
  const typingTimeoutRef = useRef(null);
  const fileInputRef = useRef(null);

  // Get current user
  useEffect(() => {
    const user = JSON.parse(localStorage.getItem('loopync_user') || '{}');
    if (!user.id) {
      navigate('/auth');
      return;
    }
    setCurrentUser(user);
    loadThreads(user.id);
    
    // Check if thread was passed from navigation
    if (location.state?.selectedThread) {
      setSelectedThread(location.state.selectedThread);
      loadMessages(location.state.selectedThread.id);
    }
  }, [navigate, location]);

  // WebSocket listeners
  useEffect(() => {
    if (!socket || !currentUser) return;

    // New message
    socket.on('new_message', (data) => {
      console.log('📨 New message received:', data);
      
      // Update threads list
      setThreads(prev => {
        const updated = prev.map(t => 
          t.id === data.threadId 
            ? { ...t, lastMessage: data.message, lastMessageAt: data.message.createdAt }
            : t
        );
        return updated.sort((a, b) => 
          new Date(b.lastMessageAt) - new Date(a.lastMessageAt)
        );
      });

      // Add to messages if thread is open
      if (selectedThread?.id === data.threadId) {
        setMessages(prev => [...prev, data.message]);
        scrollToBottom();
        
        // Mark as read
        markMessagesRead(data.threadId, [data.message.id]);
      }
    });

    // Typing indicator
    socket.on('user_typing', (data) => {
      if (selectedThread?.id === data.threadId) {
        setOtherUserTyping(data.typing);
        if (data.typing) {
          setTimeout(() => setOtherUserTyping(false), 3000);
        }
      }
    });

    // Message read
    socket.on('message_read', (data) => {
      setMessages(prev => 
        prev.map(m => 
          m.id === data.messageId 
            ? { ...m, read: true, readAt: data.readAt }
            : m
        )
      );
    });

    return () => {
      socket.off('new_message');
      socket.off('user_typing');
      socket.off('message_read');
    };
  }, [socket, currentUser, selectedThread]);

  const loadThreads = async (userId) => {
    try {
      const res = await axios.get(`${API}/messenger/threads?userId=${userId}`);
      setThreads(res.data.threads || []);
    } catch (error) {
      console.error('Error loading threads:', error);
      toast.error('Failed to load conversations');
    }
  };

  const searchFriends = async (query) => {
    if (!query.trim()) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }

    setIsSearching(true);
    try {
      // Get user's friends
      const friendsRes = await axios.get(`${API}/messenger/friends?userId=${currentUser.id}`);
      const friends = friendsRes.data.friends || [];

      // Filter friends by name
      const filtered = friends.filter(friend => 
        friend.name.toLowerCase().includes(query.toLowerCase())
      );

      setSearchResults(filtered);
    } catch (error) {
      console.error('Error searching friends:', error);
      setSearchResults([]);
    }
  };

  const handleSearchChange = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    searchFriends(query);
  };

  const startChatWithFriend = async (friend) => {
    try {
      // Check if thread already exists
      const existingThread = threads.find(t => 
        t.otherUser?.id === friend.id
      );

      if (existingThread) {
        // Open existing thread
        selectThread(existingThread);
        setSearchQuery('');
        setSearchResults([]);
        setIsSearching(false);
        return;
      }

      // Create new thread
      const res = await axios.post(
        `${API}/messenger/start?userId=${currentUser.id}&friendId=${friend.id}`
      );

      if (res.data.success) {
        const newThread = res.data.thread;
        
        // Add to threads list
        setThreads(prev => [newThread, ...prev]);
        
        // Select the new thread
        selectThread(newThread);
        
        // Clear search
        setSearchQuery('');
        setSearchResults([]);
        setIsSearching(false);
        
        toast.success(`Started chat with ${friend.name}`);
      }
    } catch (error) {
      console.error('Error starting chat:', error);
      toast.error(error.response?.data?.detail || 'Failed to start conversation');
    }
  };

  const loadMessages = async (threadId) => {
    try {
      const res = await axios.get(`${API}/messenger/threads/${threadId}/messages?limit=50`);
      setMessages(res.data.messages || []);
      setTimeout(scrollToBottom, 100);
      
      // Mark as read
      const unreadIds = res.data.messages
        .filter(m => m.recipientId === currentUser.id && !m.read)
        .map(m => m.id);
      if (unreadIds.length > 0) {
        markMessagesRead(threadId, unreadIds);
      }
    } catch (error) {
      console.error('Error loading messages:', error);
      toast.error('Failed to load messages');
    }
  };

  const selectThread = (thread) => {
    setSelectedThread(thread);
    loadMessages(thread.id);
  };

  const sendMessage = async (e) => {
    e?.preventDefault();
    if (!messageText.trim() || !selectedThread) return;

    const text = messageText.trim();
    setMessageText('');

    try {
      await axios.post(`${API}/messenger/send`, {
        senderId: currentUser.id,
        recipientId: selectedThread.otherUser.id,
        text
      });

      // Stop typing indicator
      emitTyping(false);
    } catch (error) {
      console.error('Error sending message:', error);
      toast.error('Failed to send message');
    }
  };

  const handleTyping = (e) => {
    setMessageText(e.target.value);

    if (!selectedThread) return;

    // Emit typing indicator
    emitTyping(true);

    // Clear previous timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    // Set timeout to stop typing
    typingTimeoutRef.current = setTimeout(() => {
      emitTyping(false);
    }, 2000);
  };

  const emitTyping = (typing) => {
    if (socket && selectedThread) {
      socket.emit('typing', {
        threadId: selectedThread.id,
        typing
      });
    }
  };

  const markMessagesRead = async (threadId, messageIds) => {
    try {
      await axios.post(
        `${API}/messenger/threads/${threadId}/read?userId=${currentUser.id}`,
        { messageIds }
      );
    } catch (error) {
      console.error('Error marking read:', error);
    }
  };

  const getAISuggestion = async () => {
    if (!messageText.trim()) {
      toast.error('Type a message first');
      return;
    }

    setAiLoading(true);
    try {
      const res = await axios.post(
        `${API}/messenger/ai/suggest?userId=${currentUser.id}`,
        { message: messageText }
      );
      setMessageText(res.data.suggestion);
      toast.success('AI suggestion applied!');
    } catch (error) {
      console.error('AI error:', error);
      toast.error('AI suggestion failed');
    } finally {
      setAiLoading(false);
    }
  };

  const initiateCall = async (callType) => {
    if (!selectedThread) return;

    try {
      await axios.post(`${API}/calls/initiate`, {
        callerId: currentUser.id,
        recipientId: selectedThread.otherUser.id,
        callType
      });
    } catch (error) {
      console.error('Error initiating call:', error);
      toast.error('Failed to initiate call');
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const filteredThreads = threads.filter(t => 
    t.otherUser?.name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex h-screen bg-black">
      {/* Call Manager */}
      <CallManager currentUser={currentUser} />

      {/* Threads List */}
      <div className={`${
        selectedThread ? 'hidden md:flex' : 'flex'
      } w-full md:w-96 flex-col border-r border-gray-800`}>
        {/* Header */}
        <div className="p-4 border-b border-gray-800">
          <div className="flex items-center justify-between mb-4">
            <button onClick={() => navigate('/')} className="text-white">
              <ArrowLeft size={24} />
            </button>
            <h1 className="text-xl font-bold text-white">Messages</h1>
            <button className="text-white">
              <MoreVertical size={24} />
            </button>
          </div>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-3 text-gray-500" size={20} />
            <input
              type="text"
              placeholder="Search conversations"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-900 text-white rounded-full focus:outline-none focus:ring-2 focus:ring-cyan-400"
            />
          </div>
        </div>

        {/* Threads */}
        <div className="flex-1 overflow-y-auto">
          {filteredThreads.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <p>No conversations yet</p>
              <p className="text-sm mt-2">Start chatting with your friends!</p>
            </div>
          ) : (
            filteredThreads.map(thread => (
              <div
                key={thread.id}
                onClick={() => selectThread(thread)}
                className={`flex items-center gap-3 p-4 cursor-pointer hover:bg-gray-900 transition ${
                  selectedThread?.id === thread.id ? 'bg-gray-900' : ''
                }`}
              >
                <div className="relative">
                  <img
                    src={thread.otherUser?.avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${thread.otherUser?.id}`}
                    alt={thread.otherUser?.name}
                    className="w-14 h-14 rounded-full object-cover"
                  />
                  {thread.otherUser?.online && (
                    <div className="absolute bottom-0 right-0 w-4 h-4 bg-green-500 rounded-full border-2 border-black"></div>
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <p className="font-semibold text-white truncate">
                      {thread.otherUser?.name || 'Unknown'}
                    </p>
                    {thread.lastMessage && (
                      <span className="text-xs text-gray-500">
                        {new Date(thread.lastMessage.createdAt).toLocaleTimeString([], { 
                          hour: '2-digit', 
                          minute: '2-digit' 
                        })}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-gray-400 truncate">
                      {thread.lastMessage?.text || 'No messages yet'}
                    </p>
                    {thread.unreadCount > 0 && (
                      <span className="ml-2 bg-cyan-400 text-black text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                        {thread.unreadCount}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Messages Area */}
      {selectedThread ? (
        <div className="flex-1 flex flex-col">
          {/* Chat Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-800">
            <div className="flex items-center gap-3">
              <button 
                onClick={() => setSelectedThread(null)} 
                className="md:hidden text-white"
              >
                <ArrowLeft size={24} />
              </button>
              <img
                src={selectedThread.otherUser?.avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${selectedThread.otherUser?.id}`}
                alt={selectedThread.otherUser?.name}
                className="w-10 h-10 rounded-full object-cover"
              />
              <div>
                <p className="font-semibold text-white">
                  {selectedThread.otherUser?.name}
                </p>
                {otherUserTyping ? (
                  <p className="text-xs text-cyan-400">typing...</p>
                ) : (
                  <p className="text-xs text-gray-500">
                    {selectedThread.otherUser?.online ? 'Active now' : 'Offline'}
                  </p>
                )}
              </div>
            </div>

            <div className="flex items-center gap-4">
              <button 
                onClick={() => initiateCall('audio')}
                className="text-cyan-400 hover:text-cyan-300"
              >
                <Phone size={24} />
              </button>
              <button 
                onClick={() => initiateCall('video')}
                className="text-cyan-400 hover:text-cyan-300"
              >
                <Video size={24} />
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message, idx) => {
              const isOwn = message.senderId === currentUser.id;
              const showAvatar = idx === 0 || messages[idx - 1]?.senderId !== message.senderId;

              return (
                <div
                  key={message.id}
                  className={`flex items-end gap-2 ${
                    isOwn ? 'flex-row-reverse' : 'flex-row'
                  }`}
                >
                  {!isOwn && showAvatar ? (
                    <img
                      src={message.sender?.avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${message.senderId}`}
                      alt=""
                      className="w-6 h-6 rounded-full"
                    />
                  ) : (
                    <div className="w-6" />
                  )}

                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-2 rounded-2xl ${
                      isOwn
                        ? 'bg-gradient-to-r from-cyan-400 to-blue-500 text-black'
                        : 'bg-gray-800 text-white'
                    }`}
                  >
                    {message.text && <p className="text-sm">{message.text}</p>}
                    {message.mediaUrl && (
                      <img
                        src={message.mediaUrl}
                        alt=""
                        className="rounded-lg mt-2 max-w-full"
                      />
                    )}
                  </div>

                  {isOwn && (
                    <div className="text-cyan-400">
                      {message.read ? (
                        <CheckCheck size={14} />
                      ) : (
                        <Check size={14} />
                      )}
                    </div>
                  )}
                </div>
              );
            })}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form onSubmit={sendMessage} className="p-4 border-t border-gray-800">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="text-cyan-400 hover:text-cyan-300"
              >
                <Image size={24} />
              </button>
              
              <button
                type="button"
                onClick={getAISuggestion}
                disabled={aiLoading}
                className="text-cyan-400 hover:text-cyan-300 disabled:opacity-50"
                title="AI Suggest"
              >
                <Sparkles size={24} className={aiLoading ? 'animate-spin' : ''} />
              </button>

              <input
                type="file"
                ref={fileInputRef}
                className="hidden"
                accept="image/*,video/*"
              />

              <input
                type="text"
                placeholder="Message..."
                value={messageText}
                onChange={handleTyping}
                className="flex-1 px-4 py-2 bg-gray-900 text-white rounded-full focus:outline-none focus:ring-2 focus:ring-cyan-400"
              />

              {messageText.trim() ? (
                <button
                  type="submit"
                  className="text-cyan-400 hover:text-cyan-300 font-semibold"
                >
                  Send
                </button>
              ) : (
                <button type="button" className="text-cyan-400 hover:text-cyan-300">
                  <Mic size={24} />
                </button>
              )}
            </div>
          </form>
        </div>
      ) : (
        <div className="hidden md:flex flex-1 items-center justify-center text-gray-500">
          <div className="text-center">
            <div className="w-24 h-24 mx-auto mb-4 rounded-full border-4 border-gray-800 flex items-center justify-center">
              <Send size={40} className="text-gray-700" />
            </div>
            <h2 className="text-2xl font-bold mb-2">Your Messages</h2>
            <p>Send private messages to your friends</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default MessengerNew;