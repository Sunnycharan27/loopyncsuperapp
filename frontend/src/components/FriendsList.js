import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { MessageCircle, Phone, Video, UserPlus, UserCheck, UserX, X } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const FriendsList = ({ currentUser, onStartChat, onStartCall }) => {
  const navigate = useNavigate();
  const [friends, setFriends] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [pendingRequests, setPendingRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('friends'); // 'friends', 'suggestions', 'requests'

  useEffect(() => {
    if (currentUser?.id) {
      loadData();
    }
  }, [currentUser]);

  const loadData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadFriends(),
        loadSuggestions(),
        loadPendingRequests()
      ]);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadFriends = async () => {
    try {
      const res = await axios.get(`${API}/friends/${currentUser.id}`);
      const friendsData = res.data.friends || [];
      
      // Get messaging status for each friend
      const friendsWithStatus = await Promise.all(
        friendsData.map(async (friend) => {
          try {
            // Check if thread exists
            const participants = [currentUser.id, friend.id].sort();
            const threadRes = await axios.get(
              `${API}/messenger/threads?userId=${currentUser.id}`
            );
            const threads = threadRes.data.threads || [];
            const existingThread = threads.find(t => 
              t.participants.includes(friend.id)
            );
            
            return {
              ...friend,
              hasThread: !!existingThread,
              threadId: existingThread?.id
            };
          } catch (error) {
            return { ...friend, hasThread: false };
          }
        })
      );
      
      setFriends(friendsWithStatus);
    } catch (error) {
      console.error('Error loading friends:', error);
    }
  };

  const loadSuggestions = async () => {
    try {
      // Get all users except current user and existing friends
      const usersRes = await axios.get(`${API}/users`);
      const allUsers = usersRes.data.users || [];
      
      const friendIds = friends.map(f => f.id);
      const suggestions = allUsers
        .filter(u => u.id !== currentUser.id && !friendIds.includes(u.id))
        .slice(0, 10);
      
      setSuggestions(suggestions);
    } catch (error) {
      console.error('Error loading suggestions:', error);
    }
  };

  const loadPendingRequests = async () => {
    try {
      const user = await axios.get(`${API}/users/${currentUser.id}`);
      const requests = user.data.friendRequestsReceived || [];
      
      // Get user details for each request
      const requestsWithDetails = await Promise.all(
        requests.map(async (userId) => {
          const userRes = await axios.get(`${API}/users/${userId}`);
          return userRes.data;
        })
      );
      
      setPendingRequests(requestsWithDetails);
    } catch (error) {
      console.error('Error loading requests:', error);
    }
  };

  const sendFriendRequest = async (userId) => {
    try {
      await axios.post(`${API}/friends/request`, {
        senderId: currentUser.id,
        receiverId: userId
      });
      toast.success('Friend request sent!');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send request');
    }
  };

  const acceptFriendRequest = async (userId) => {
    try {
      await axios.post(`${API}/friends/accept`, {
        userId: currentUser.id,
        friendId: userId
      });
      toast.success('Friend request accepted!');
      loadData();
    } catch (error) {
      toast.error('Failed to accept request');
    }
  };

  const rejectFriendRequest = async (userId) => {
    try {
      await axios.post(`${API}/friends/reject`, {
        userId: currentUser.id,
        friendId: userId
      });
      toast.info('Friend request rejected');
      loadData();
    } catch (error) {
      toast.error('Failed to reject request');
    }
  };

  const startConversation = async (friend) => {
    try {
      const res = await axios.post(
        `${API}/messenger/start?userId=${currentUser.id}&friendId=${friend.id}`
      );
      
      if (res.data.success) {
        // Navigate to messenger with the thread
        navigate('/messenger', { state: { selectedThread: res.data.thread } });
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to start conversation');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400"></div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-4">
      {/* Tabs */}
      <div className="flex gap-4 border-b border-gray-800 mb-6">
        <button
          onClick={() => setActiveTab('friends')}
          className={`px-4 py-2 font-semibold transition ${
            activeTab === 'friends'
              ? 'text-cyan-400 border-b-2 border-cyan-400'
              : 'text-gray-500 hover:text-white'
          }`}
        >
          Friends ({friends.length})
        </button>
        <button
          onClick={() => setActiveTab('requests')}
          className={`px-4 py-2 font-semibold transition relative ${
            activeTab === 'requests'
              ? 'text-cyan-400 border-b-2 border-cyan-400'
              : 'text-gray-500 hover:text-white'
          }`}
        >
          Requests
          {pendingRequests.length > 0 && (
            <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center">
              {pendingRequests.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('suggestions')}
          className={`px-4 py-2 font-semibold transition ${
            activeTab === 'suggestions'
              ? 'text-cyan-400 border-b-2 border-cyan-400'
              : 'text-gray-500 hover:text-white'
          }`}
        >
          Suggestions
        </button>
      </div>

      {/* Friends Tab */}
      {activeTab === 'friends' && (
        <div className="space-y-4">
          {friends.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <p>No friends yet</p>
              <p className="text-sm mt-2">Check out suggestions to add friends!</p>
            </div>
          ) : (
            friends.map((friend) => (
              <div
                key={friend.id}
                className="flex items-center gap-4 p-4 bg-gray-900 rounded-xl hover:bg-gray-800 transition"
              >
                <img
                  src={friend.avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${friend.id}`}
                  alt={friend.name}
                  className="w-16 h-16 rounded-full object-cover"
                />
                <div className="flex-1">
                  <h3 className="font-semibold text-white">{friend.name}</h3>
                  <p className="text-sm text-gray-400">@{friend.handle || 'user'}</p>
                  {friend.online && (
                    <p className="text-xs text-green-400 mt-1">● Online</p>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => startConversation(friend)}
                    className="p-3 rounded-full bg-cyan-400 text-black hover:bg-cyan-500 transition"
                    title="Send Message"
                  >
                    <MessageCircle size={20} />
                  </button>
                  <button
                    onClick={() => onStartCall?.(friend.id, 'audio')}
                    className="p-3 rounded-full bg-green-500 text-white hover:bg-green-600 transition"
                    title="Voice Call"
                  >
                    <Phone size={20} />
                  </button>
                  <button
                    onClick={() => onStartCall?.(friend.id, 'video')}
                    className="p-3 rounded-full bg-blue-500 text-white hover:bg-blue-600 transition"
                    title="Video Call"
                  >
                    <Video size={20} />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Requests Tab */}
      {activeTab === 'requests' && (
        <div className="space-y-4">
          {pendingRequests.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <p>No pending requests</p>
            </div>
          ) : (
            pendingRequests.map((user) => (
              <div
                key={user.id}
                className="flex items-center gap-4 p-4 bg-gray-900 rounded-xl"
              >
                <img
                  src={user.avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${user.id}`}
                  alt={user.name}
                  className="w-16 h-16 rounded-full object-cover"
                />
                <div className="flex-1">
                  <h3 className="font-semibold text-white">{user.name}</h3>
                  <p className="text-sm text-gray-400">wants to connect with you</p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => acceptFriendRequest(user.id)}
                    className="px-4 py-2 rounded-full bg-cyan-400 text-black hover:bg-cyan-500 transition font-semibold"
                  >
                    Accept
                  </button>
                  <button
                    onClick={() => rejectFriendRequest(user.id)}
                    className="p-2 rounded-full bg-gray-700 text-white hover:bg-gray-600 transition"
                  >
                    <X size={20} />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Suggestions Tab */}
      {activeTab === 'suggestions' && (
        <div className="space-y-4">
          {suggestions.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <p>No suggestions available</p>
            </div>
          ) : (
            suggestions.map((user) => (
              <div
                key={user.id}
                className="flex items-center gap-4 p-4 bg-gray-900 rounded-xl hover:bg-gray-800 transition"
              >
                <img
                  src={user.avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${user.id}`}
                  alt={user.name}
                  className="w-16 h-16 rounded-full object-cover"
                />
                <div className="flex-1">
                  <h3 className="font-semibold text-white">{user.name}</h3>
                  <p className="text-sm text-gray-400">@{user.handle || 'user'}</p>
                </div>
                <button
                  onClick={() => sendFriendRequest(user.id)}
                  className="px-4 py-2 rounded-full bg-cyan-400 text-black hover:bg-cyan-500 transition font-semibold flex items-center gap-2"
                >
                  <UserPlus size={18} />
                  Add Friend
                </button>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default FriendsList;
