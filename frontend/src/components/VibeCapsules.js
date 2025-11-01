import React, { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import VibeCapsuleUpload from "./VibeCapsuleUpload";
import VibeCapsuleViewer from "./VibeCapsuleViewer";

const VibeCapsules = ({ currentUser }) => {
  const [stories, setStories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedStoryIndex, setSelectedStoryIndex] = useState(null);

  useEffect(() => {
    fetchCapsules();
  }, []);

  const fetchCapsules = async () => {
    try {
      setLoading(true);
      // Fetch public capsules (no userId needed for public feed)
      const response = await axios.get(`${API}/capsules`);
      setStories(response.data.stories || []);
    } catch (error) {
      console.error("Failed to fetch capsules:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleStoryClick = (index) => {
    setSelectedStoryIndex(index);
  };

  const handleCloseViewer = () => {
    setSelectedStoryIndex(null);
    fetchCapsules(); // Refresh after viewing
  };

  if (loading) {
    return (
      <div className="px-4 py-3">
        <div className="flex gap-4 overflow-x-auto hide-scrollbar">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="flex flex-col items-center gap-2 flex-shrink-0 animate-pulse">
              <div className="w-16 h-16 rounded-full bg-gray-800" />
              <div className="w-12 h-3 bg-gray-800 rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="px-4 py-3 border-b border-gray-800">
        <div className="flex gap-4 overflow-x-auto hide-scrollbar pb-2">
          {/* Stories from all users (including current user) */}
          {currentUser && stories.length > 0 && (
            <>
              {/* Check if current user has a story */}
              {(() => {
                const userStoryIndex = stories.findIndex(s => s.author.id === currentUser.id);
                const hasUserStory = userStoryIndex !== -1;
                
                if (hasUserStory) {
                  // Show current user's story first with special styling
                  const userStory = stories[userStoryIndex];
                  return (
                    <button
                      onClick={() => handleStoryClick(userStoryIndex)}
                      className="flex flex-col items-center gap-2 flex-shrink-0"
                    >
                      <div className="relative">
                        <div className="w-16 h-16 rounded-full bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-500 p-0.5">
                          <div className="w-full h-full rounded-full border-4 border-gray-900 overflow-hidden">
                            <img
                              src={userStory.author.avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${currentUser.name}`}
                              alt="Your Story"
                              className="w-full h-full object-cover"
                            />
                          </div>
                        </div>
                        {/* Add Story indicator on top of user's story */}
                        <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 border-2 border-gray-900 flex items-center justify-center">
                          <span className="text-white text-xs font-bold">+</span>
                        </div>
                        {userStory.capsules.length > 1 && (
                          <div className="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-gradient-to-r from-pink-500 to-purple-500 border-2 border-gray-900 flex items-center justify-center">
                            <span className="text-white text-xs font-bold">{userStory.capsules.length}</span>
                          </div>
                        )}
                      </div>
                      <span className="text-xs text-cyan-400 font-semibold">Your Story</span>
                    </button>
                  );
                } else {
                  // Show upload button if user has no story
                  return (
                    <VibeCapsuleUpload 
                      currentUser={currentUser} 
                      onUploadComplete={fetchCapsules}
                    />
                  );
                }
              })()}
              
              {/* Other users' stories */}
              {stories.filter(s => s.author.id !== currentUser.id).map((story, index) => {
                // Find the actual index in the full stories array
                const actualIndex = stories.findIndex(s => s.author.id === story.author.id);
                return (
                  <button
                    key={story.author.id}
                    onClick={() => handleStoryClick(actualIndex)}
                    className="flex flex-col items-center gap-2 flex-shrink-0"
                  >
                    <div className="relative">
                      <div className="w-16 h-16 rounded-full bg-gradient-to-r from-pink-500 via-purple-500 to-cyan-500 p-0.5">
                        <div className="w-full h-full rounded-full border-4 border-gray-900 overflow-hidden">
                          <img
                            src={story.author.avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${story.author.name}`}
                            alt={story.author.name}
                            className="w-full h-full object-cover"
                          />
                        </div>
                      </div>
                      {story.capsules.length > 1 && (
                        <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 border-2 border-gray-900 flex items-center justify-center">
                          <span className="text-white text-xs font-bold">{story.capsules.length}</span>
                        </div>
                      )}
                    </div>
                    <span className="text-xs text-white font-medium max-w-[60px] truncate">
                      {story.author.name.split(' ')[0]}
                    </span>
                  </button>
                );
              })}
            </>
          )}

          {/* If no stories at all, show upload button */}
          {currentUser && stories.length === 0 && (
            <VibeCapsuleUpload 
              currentUser={currentUser} 
              onUploadComplete={fetchCapsules}
            />
          )}

          {/* Empty State */}
          {stories.length === 0 && (
            <div className="flex items-center justify-center text-gray-500 text-sm py-4">
              No stories yet. Be the first to share!
            </div>
          )}
        </div>
      </div>

      {/* Story Viewer */}
      {selectedStoryIndex !== null && (
        <VibeCapsuleViewer
          stories={stories}
          currentUserId={currentUser.id}
          onClose={handleCloseViewer}
        />
      )}

      <style jsx>{`
        .hide-scrollbar::-webkit-scrollbar {
          display: none;
        }
        .hide-scrollbar {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}</style>
    </>
  );
};

export default VibeCapsules;
