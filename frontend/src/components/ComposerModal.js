import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import { X, Image as ImageIcon, Upload, Cloud } from "lucide-react";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const CLOUDINARY_CLOUD = process.env.REACT_APP_CLOUDINARY_CLOUD;
const CLOUDINARY_PRESET = process.env.REACT_APP_CLOUDINARY_UNSIGNED || 'loopync_unsigned';

const ComposerModal = ({ currentUser, onClose, onPostCreated }) => {
  const [text, setText] = useState("");
  const [media, setMedia] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadMethod, setUploadMethod] = useState("local"); // "local" or "cloudinary"
  const fileInputRef = useRef(null);
  const widgetRef = useRef(null);

  useEffect(() => {
    // Load Cloudinary widget script if configured
    if (CLOUDINARY_CLOUD) {
      const script = document.createElement('script');
      script.src = 'https://upload-widget.cloudinary.com/global/all.js';
      script.async = true;
      document.body.appendChild(script);

      return () => {
        if (document.body.contains(script)) {
          document.body.removeChild(script);
        }
      };
    }
  }, []);

  const openCloudinaryWidget = () => {
    if (window.cloudinary && CLOUDINARY_CLOUD) {
      widgetRef.current = window.cloudinary.createUploadWidget(
        {
          cloudName: CLOUDINARY_CLOUD,
          uploadPreset: CLOUDINARY_PRESET,
          folder: 'loopync/posts',
          sources: ['local', 'camera'],
          resourceType: 'image',
          maxFileSize: 10000000,
          clientAllowedFormats: ['jpg', 'jpeg', 'png', 'gif', 'webp'],
          showPoweredBy: false,
          styles: {
            palette: {
              window: '#121427',
              sourceBg: '#0f021e',
              windowBorder: '#00E0FF',
              tabIcon: '#00E0FF',
              inactiveTabIcon: '#555',
              menuIcons: '#00E0FF',
              link: '#00E0FF',
              action: '#00E0FF',
              inProgress: '#00E0FF',
              complete: '#5AFF9C',
              error: '#FF3DB3',
              textDark: '#FFFFFF',
              textLight: '#FFFFFF'
            }
          }
        },
        (error, result) => {
          if (!error && result && result.event === 'success') {
            setMedia(result.info.secure_url);
            setPreviewUrl(result.info.secure_url);
            setUploadMethod('cloudinary');
            toast.success('Image uploaded to Cloudinary!');
          }
        }
      );
      widgetRef.current.open();
    } else {
      toast.error('Cloudinary not configured');
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file size (max 50MB for videos, 10MB for images)
    const maxSize = file.type.startsWith('video/') ? 50 * 1024 * 1024 : 10 * 1024 * 1024;
    if (file.size > maxSize) {
      toast.error(`File size must be less than ${maxSize / (1024 * 1024)}MB`);
      return;
    }

    // Validate file type
    const allowedTypes = [
      'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp',
      'video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/webm'
    ];
    if (!allowedTypes.includes(file.type)) {
      toast.error("Only images (JPEG, PNG, GIF, WebP) and videos (MP4, MOV, AVI, WebM) are supported");
      return;
    }

    setSelectedFile(file);
    
    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setPreviewUrl(reader.result);
    };
    reader.readAsDataURL(file);
    
    toast.success(`${file.type.startsWith('video/') ? 'Video' : 'Image'} selected!`);
  };

  const handleUpload = async () => {
    if (!selectedFile) return null;

    setUploading(true);
    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      console.log('Uploading file to:', `${API}/upload`);
      const res = await axios.post(`${API}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 60000 // 60 second timeout for large files
      });
      
      console.log('Upload response:', res.data);
      
      // The backend returns { url: "/uploads/filename.jpg" }
      // We need to return just the path, not the full URL
      const uploadedPath = res.data.url;
      console.log('Uploaded path:', uploadedPath);
      
      toast.success("Media uploaded successfully!");
      return uploadedPath; // Return just the path like "/uploads/filename.jpg"
    } catch (error) {
      console.error("Upload error:", error);
      const errorMsg = error.response?.data?.detail || error.message || "Failed to upload file";
      toast.error(`Upload failed: ${errorMsg}`);
      return null;
    } finally {
      setUploading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!text.trim()) {
      toast.error("Post text cannot be empty");
      return;
    }

    setLoading(true);
    try {
      let mediaUrl = media;
      
      // Upload file if selected
      if (selectedFile) {
        const uploadedUrl = await handleUpload();
        if (uploadedUrl) {
          mediaUrl = uploadedUrl;
        }
      }

      const res = await axios.post(`${API}/posts?authorId=${currentUser.id}`, {
        text,
        media: mediaUrl || null,
        audience: "public"
      });
      toast.success("Posted!");
      onPostCreated(res.data);
    } catch (error) {
      toast.error("Failed to create post");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="glass-card p-6 w-full max-w-xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold neon-text">Create Post</h2>
          <button
            data-testid="composer-close-btn"
            onClick={onClose}
            className="text-gray-400 hover:text-white"
          >
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <textarea
            data-testid="composer-text-input"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="What's on your mind?"
            className="w-full h-32 resize-none mb-4"
            autoFocus
          />

          {/* File Upload Section */}
          <div className="mb-4">
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/jpg,image/png,image/gif,image/webp,video/mp4,video/quicktime,video/x-msvideo,video/webm"
              onChange={handleFileSelect}
              className="hidden"
            />
            
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-full bg-cyan-400/10 text-cyan-400 hover:bg-cyan-400/20"
                data-testid="composer-file-btn"
              >
                <Upload size={18} />
                {selectedFile ? "Change Photo" : "Upload from Device"}
              </button>
              
              {CLOUDINARY_CLOUD && (
                <button
                  type="button"
                  onClick={openCloudinaryWidget}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-full bg-purple-400/10 text-purple-400 hover:bg-purple-400/20"
                  data-testid="composer-cloudinary-btn"
                >
                  <Cloud size={18} />
                  Upload to Cloud
                </button>
              )}
            </div>
          </div>

          {/* Preview */}
          {previewUrl && (
            <div className="mb-4 relative">
              <img src={previewUrl} alt="Preview" className="rounded-2xl w-full max-h-64 object-cover" />
              <button
                type="button"
                onClick={() => {
                  setSelectedFile(null);
                  setPreviewUrl("");
                }}
                className="absolute top-2 right-2 w-8 h-8 rounded-full bg-black/50 flex items-center justify-center text-white hover:bg-black/70"
              >
                <X size={18} />
              </button>
            </div>
          )}

          {/* URL Input (optional fallback) */}
          {!selectedFile && (
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2 text-gray-400">
                <ImageIcon size={16} className="inline mr-2" />
                Or paste image URL (optional)
              </label>
              <input
                data-testid="composer-media-input"
                type="url"
                value={media}
                onChange={(e) => setMedia(e.target.value)}
                placeholder="https://example.com/image.jpg"
                className="w-full"
              />
            </div>
          )}

          {media && !selectedFile && (
            <div className="mb-4">
              <img src={media} alt="Preview" className="rounded-2xl w-full max-h-64 object-cover" onError={() => setMedia("")} />
            </div>
          )}

          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-3 rounded-full border border-gray-600 text-gray-300 hover:bg-gray-800"
            >
              Cancel
            </button>
            <button
              data-testid="composer-submit-btn"
              type="submit"
              disabled={loading || uploading || !text.trim()}
              className="flex-1 btn-primary"
            >
              {uploading ? "Uploading..." : loading ? "Posting..." : "Post"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ComposerModal;