"""
Complete Messenger Service - Instagram-style messaging with AI features
Handles: DMs, Real-time messaging, Audio/Video calls, Media sharing, AI assistance
"""

import os
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict
from fastapi import HTTPException
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorDatabase
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

# ===== PYDANTIC MODELS =====

class SendMessageRequest(BaseModel):
    senderId: str
    recipientId: str
    text: Optional[str] = None
    mediaUrl: Optional[str] = None
    mediaType: Optional[str] = None  # 'image', 'video', 'audio', 'file'
    replyToId: Optional[str] = None

class AIMessageRequest(BaseModel):
    message: str
    context: Optional[str] = None

class MessageReaction(BaseModel):
    userId: str
    reaction: str  # 'like', 'love', 'haha', 'wow', 'sad', 'angry'

class UpdateReadStatusRequest(BaseModel):
    messageIds: List[str]

# ===== MESSENGER SERVICE =====

class MessengerService:
    def __init__(self, db: AsyncIOMotorDatabase, emit_to_user_func):
        self.db = db
        self.emit_to_user = emit_to_user_func
        self.llm_key = os.environ.get('EMERGENT_LLM_KEY')
        self.ai_sessions = {}  # Store AI chat sessions
        
    async def get_or_create_thread(self, user1_id: str, user2_id: str) -> dict:
        """Get existing thread or create new one between two users"""
        # Check if users are friends
        are_friends = await self.check_friendship(user1_id, user2_id)
        if not are_friends:
            raise HTTPException(status_code=403, detail="You can only message friends. Send a friend request first!")
        
        # Sort user IDs to ensure consistent thread lookup
        participants = sorted([user1_id, user2_id])
        
        # Try to find existing thread
        thread = await self.db.threads.find_one({
            "participants": participants,
            "type": "direct"
        }, {"_id": 0})
        
        if thread:
            return thread
        
        # Create new thread
        thread = {
            "id": str(uuid.uuid4()),
            "participants": participants,
            "type": "direct",
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "lastMessageAt": datetime.now(timezone.utc).isoformat(),
            "lastMessage": None,
            "unreadCount": {user1_id: 0, user2_id: 0}
        }
        
        await self.db.threads.insert_one(thread)
        logger.info(f"Created new thread {thread['id']} between {user1_id} and {user2_id}")
        
        return thread
    
    async def check_friendship(self, user1_id: str, user2_id: str) -> bool:
        """Check if two users are friends"""
        user1 = await self.db.users.find_one({"id": user1_id})
        if not user1:
            return False
        
        friends = user1.get("friends", [])
        return user2_id in friends
    
    async def send_message(self, request: SendMessageRequest) -> dict:
        """Send a message in a thread"""
        # Get or create thread
        thread = await self.get_or_create_thread(request.senderId, request.recipientId)
        
        # Create message
        message = {
            "id": str(uuid.uuid4()),
            "threadId": thread["id"],
            "senderId": request.senderId,
            "recipientId": request.recipientId,
            "text": request.text,
            "mediaUrl": request.mediaUrl,
            "mediaType": request.mediaType,
            "replyToId": request.replyToId,
            "reactions": [],
            "read": False,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.messages.insert_one(message)
        
        # Update thread last message
        await self.db.threads.update_one(
            {"id": thread["id"]},
            {
                "$set": {
                    "lastMessage": {
                        "id": message["id"],
                        "text": message["text"],
                        "senderId": message["senderId"],
                        "createdAt": message["createdAt"]
                    },
                    "lastMessageAt": message["createdAt"]
                },
                "$inc": {f"unreadCount.{request.recipientId}": 1}
            }
        )
        
        # Enrich message with sender info
        sender = await self.db.users.find_one({"id": request.senderId}, {"_id": 0})
        message["sender"] = {
            "id": sender["id"],
            "name": sender.get("name", "Unknown"),
            "avatar": sender.get("avatar", "")
        }
        
        # Emit real-time event to recipient
        await self.emit_to_user(request.recipientId, 'new_message', {
            "threadId": thread["id"],
            "message": message
        })
        
        logger.info(f"Message sent from {request.senderId} to {request.recipientId}")
        
        return message
    
    async def get_threads(self, user_id: str) -> List[dict]:
        """Get all message threads for a user"""
        threads = await self.db.threads.find({
            "participants": user_id
        }).sort("lastMessageAt", -1).to_list(100)
        
        # Enrich with participant info
        for thread in threads:
            # Get other participant
            other_user_id = [p for p in thread["participants"] if p != user_id][0]
            other_user = await self.db.users.find_one({"id": other_user_id}, {"_id": 0})
            
            if other_user:
                thread["otherUser"] = {
                    "id": other_user["id"],
                    "name": other_user.get("name", "Unknown"),
                    "avatar": other_user.get("avatar", ""),
                    "online": other_user.get("online", False)
                }
            
            # Get unread count for this user
            thread["unreadCount"] = thread.get("unreadCount", {}).get(user_id, 0)
        
        return threads
    
    async def get_messages(self, thread_id: str, limit: int = 50, before: Optional[str] = None) -> List[dict]:
        """Get messages in a thread with pagination"""
        query = {"threadId": thread_id}
        
        if before:
            # Get messages before a certain message (for pagination)
            before_message = await self.db.messages.find_one({"id": before})
            if before_message:
                query["createdAt"] = {"$lt": before_message["createdAt"]}
        
        messages = await self.db.messages.find(query, {"_id": 0})\
            .sort("createdAt", -1)\
            .limit(limit)\
            .to_list(limit)
        
        # Reverse to get chronological order
        messages.reverse()
        
        # Enrich with sender info
        for message in messages:
            sender = await self.db.users.find_one({"id": message["senderId"]}, {"_id": 0})
            if sender:
                message["sender"] = {
                    "id": sender["id"],
                    "name": sender.get("name", "Unknown"),
                    "avatar": sender.get("avatar", "")
                }
        
        return messages
    
    async def mark_messages_read(self, user_id: str, thread_id: str, message_ids: List[str]):
        """Mark messages as read"""
        # Update messages
        await self.db.messages.update_many(
            {
                "id": {"$in": message_ids},
                "recipientId": user_id,
                "read": False
            },
            {"$set": {"read": True, "readAt": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Reset unread count for this thread
        await self.db.threads.update_one(
            {"id": thread_id},
            {"$set": {f"unreadCount.{user_id}": 0}}
        )
        
        # Emit read receipt to sender
        messages = await self.db.messages.find({"id": {"$in": message_ids}}).to_list(100)
        for message in messages:
            await self.emit_to_user(message["senderId"], 'message_read', {
                "messageId": message["id"],
                "threadId": thread_id,
                "readBy": user_id,
                "readAt": datetime.now(timezone.utc).isoformat()
            })
        
        logger.info(f"Marked {len(message_ids)} messages as read in thread {thread_id}")
    
    async def add_reaction(self, message_id: str, user_id: str, reaction: str) -> dict:
        """Add reaction to a message"""
        message = await self.db.messages.find_one({"id": message_id})
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Remove existing reaction from this user
        reactions = [r for r in message.get("reactions", []) if r["userId"] != user_id]
        
        # Add new reaction
        reactions.append({
            "userId": user_id,
            "reaction": reaction,
            "createdAt": datetime.now(timezone.utc).isoformat()
        })
        
        await self.db.messages.update_one(
            {"id": message_id},
            {"$set": {"reactions": reactions}}
        )
        
        # Emit reaction event
        await self.emit_to_user(message["senderId"], 'message_reaction', {
            "messageId": message_id,
            "userId": user_id,
            "reaction": reaction
        })
        
        return {"success": True, "reactions": reactions}
    
    async def delete_message(self, message_id: str, user_id: str):
        """Delete a message (soft delete)"""
        message = await self.db.messages.find_one({"id": message_id})
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        if message["senderId"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this message")
        
        await self.db.messages.update_one(
            {"id": message_id},
            {"$set": {"deleted": True, "deletedAt": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Emit deletion event
        await self.emit_to_user(message["recipientId"], 'message_deleted', {
            "messageId": message_id,
            "threadId": message["threadId"]
        })
        
        logger.info(f"Message {message_id} deleted by {user_id}")
    
    async def get_ai_response(self, request: AIMessageRequest, user_id: str) -> str:
        """Get AI-powered message suggestion or response"""
        try:
            # Get or create AI chat session for this user
            if user_id not in self.ai_sessions:
                self.ai_sessions[user_id] = LlmChat(
                    api_key=self.llm_key,
                    session_id=f"messenger_ai_{user_id}",
                    system_message="You are a helpful AI assistant integrated into a messaging app. Provide concise, friendly responses. Keep responses under 200 words."
                ).with_model("openai", "gpt-4o-mini")
            
            chat = self.ai_sessions[user_id]
            
            # Add context if provided
            prompt = request.message
            if request.context:
                prompt = f"Context: {request.context}\n\nUser: {request.message}"
            
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            logger.info(f"AI response generated for user {user_id}")
            return response
            
        except Exception as e:
            logger.error(f"AI response error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")
    
    async def search_messages(self, user_id: str, query: str, limit: int = 20) -> List[dict]:
        """Search messages across all threads"""
        # Get user's threads
        threads = await self.db.threads.find({"participants": user_id}).to_list(100)
        thread_ids = [t["id"] for t in threads]
        
        # Search messages
        messages = await self.db.messages.find({
            "threadId": {"$in": thread_ids},
            "text": {"$regex": query, "$options": "i"},
            "deleted": {"$ne": True}
        }, {"_id": 0}).sort("createdAt", -1).limit(limit).to_list(limit)
        
        # Enrich with sender info
        for message in messages:
            sender = await self.db.users.find_one({"id": message["senderId"]}, {"_id": 0})
            if sender:
                message["sender"] = {
                    "id": sender["id"],
                    "name": sender.get("name", "Unknown"),
                    "avatar": sender.get("avatar", "")
                }
        
        return messages
