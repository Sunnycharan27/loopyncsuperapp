import React, { useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../App';
import { ArrowLeft } from 'lucide-react';
import FriendsList from '../components/FriendsList';
import axios from 'axios';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const People = () => {
  const { currentUser } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleStartCall = async (friendId, callType) => {
    try {
      await axios.post(`${API}/calls/initiate`, {
        callerId: currentUser.id,
        recipientId: friendId,
        callType
      });
      toast.success(`${callType === 'video' ? 'Video' : 'Voice'} call initiated!`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to initiate call');
    }
  };

  return (
    <div className="min-h-screen bg-black text-white pb-20">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-black/90 backdrop-blur-lg border-b border-gray-800 p-4">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate('/')} className="text-white">
            <ArrowLeft size={24} />
          </button>
          <h1 className="text-2xl font-bold">People</h1>
        </div>
      </div>

      {/* Friends List Component */}
      <FriendsList 
        currentUser={currentUser} 
        onStartCall={handleStartCall}
      />
    </div>
  );
};

export default People;
