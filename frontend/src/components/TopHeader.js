import React, { useState, useEffect } from "react";
import { MessageCircle, Bell, Mic } from "lucide-react";
import { useNavigate } from "react-router-dom";
import VoiceBotModal from "./VoiceBotModal";

const TopHeader = ({ title, subtitle, showIcons = true }) => {
  const navigate = useNavigate();
  const [showVoiceBot, setShowVoiceBot] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  // Detect mobile device
  useEffect(() => {
    const checkMobile = () => {
      const userAgent = navigator.userAgent || navigator.vendor || window.opera;
      const mobile = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent.toLowerCase());
      setIsMobile(mobile);
    };
    checkMobile();
  }, []);

  return (
    <>
      <div className="sticky top-0 z-10 bg-gray-800 border-b border-gray-700 p-4 mb-0 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <img 
            src="/loopync-logo.jpg" 
            alt="Loopync" 
            className="w-10 h-10 rounded-full cursor-pointer hover:scale-110 transition-transform"
            onClick={() => navigate('/')}
          />
          <div>
            <h1 className="text-xl font-bold text-white">{title}</h1>
            {subtitle && <p className="text-xs text-gray-400">{subtitle}</p>}
          </div>
        </div>
        
        {showIcons && (
          <div className="flex items-center gap-2">
            {/* AI Voice Bot Button - More Prominent */}
            <button
              onClick={() => setShowVoiceBot(true)}
              className="relative w-11 h-11 rounded-full flex items-center justify-center bg-gradient-to-r from-cyan-400 to-blue-500 text-black hover:from-cyan-500 hover:to-blue-600 transition-all shadow-lg shadow-cyan-400/50 hover:scale-110"
              title="AI Voice Assistant"
              aria-label="Open AI Voice Assistant"
            >
              <Mic size={22} className="drop-shadow-lg" />
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full border-2 border-gray-800 animate-pulse"></span>
            </button>

            <button
              onClick={() => navigate('/notifications')}
              className="relative w-10 h-10 rounded-full flex items-center justify-center bg-gray-700 text-white hover:bg-gray-600 transition-colors"
              data-testid="header-notifications-btn"
            >
              <Bell size={20} />
            <div className="absolute top-1 right-1 w-2 h-2 rounded-full bg-cyan-400"></div>
          </button>
          <button
            onClick={() => navigate('/messenger')}
            className="relative w-10 h-10 rounded-full flex items-center justify-center bg-gray-700 text-white hover:bg-gray-600 transition-colors"
            data-testid="header-messenger-btn"
          >
            <MessageCircle size={20} />
            <div className="absolute top-1 right-1 w-2 h-2 rounded-full bg-cyan-400"></div>
          </button>
        </div>
      )}
    </div>

    {/* Floating AI Assistant Button for Mobile */}
    {isMobile && (
      <button
        onClick={() => setShowVoiceBot(true)}
        className="fixed bottom-20 right-4 z-50 w-14 h-14 rounded-full flex items-center justify-center bg-gradient-to-r from-cyan-400 to-blue-500 text-black shadow-2xl shadow-cyan-400/50 hover:scale-110 transition-all active:scale-95"
        style={{ animation: 'bounce 2s infinite' }}
        aria-label="Open AI Assistant"
      >
        <Mic size={24} className="drop-shadow-lg" />
        <span className="absolute -top-1 -right-1 w-4 h-4 bg-green-400 rounded-full border-2 border-gray-800 animate-pulse"></span>
      </button>
    )}

    {/* Voice Bot Modal */}
    <VoiceBotModal isOpen={showVoiceBot} onClose={() => setShowVoiceBot(false)} />
  </>
  );
};

export default TopHeader;
