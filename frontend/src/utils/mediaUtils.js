/**
 * Utility functions for handling media URLs across the application
 */

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

/**
 * Converts a media URL to a full accessible URL
 * @param {string} mediaUrl - The media URL (can be relative or absolute)
 * @returns {string} - Full accessible URL
 */
export const getMediaUrl = (mediaUrl) => {
  if (!mediaUrl) return '';
  
  // If it already has http/https, return as-is (external URL or Cloudinary)
  if (mediaUrl.startsWith('http://') || mediaUrl.startsWith('https://')) {
    return mediaUrl;
  }
  
  // If it's a relative path starting with /api/uploads or /uploads, prepend backend URL
  if (mediaUrl.startsWith('/api/uploads') || mediaUrl.startsWith('/uploads')) {
    return `${BACKEND_URL}${mediaUrl}`;
  }
  
  // Default: prepend backend URL
  return `${BACKEND_URL}${mediaUrl}`;
};

/**
 * Check if a URL is a video based on file extension
 * @param {string} url - The URL to check
 * @returns {boolean} - True if it's a video URL
 */
export const isVideoUrl = (url) => {
  if (!url) return false;
  return /\.(mp4|webm|mov|avi|mkv)$/i.test(url);
};

/**
 * Check if a URL is an image based on file extension
 * @param {string} url - The URL to check
 * @returns {boolean} - True if it's an image URL
 */
export const isImageUrl = (url) => {
  if (!url) return false;
  return /\.(jpg|jpeg|png|gif|webp|bmp|svg)$/i.test(url);
};

/**
 * Get media type from URL
 * @param {string} url - The URL to check
 * @returns {string} - 'image', 'video', or 'unknown'
 */
export const getMediaType = (url) => {
  if (isVideoUrl(url)) return 'video';
  if (isImageUrl(url)) return 'image';
  return 'unknown';
};

export default {
  getMediaUrl,
  isVideoUrl,
  isImageUrl,
  getMediaType
};
