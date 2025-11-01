import { useState, useCallback, useEffect } from 'react';

export const useTextToSpeech = () => {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voices, setVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState(null);

  useEffect(() => {
    const loadVoices = () => {
      const synth = window.speechSynthesis;
      const availableVoices = synth.getVoices();
      setVoices(availableVoices);
      
      if (availableVoices.length > 0 && !selectedVoice) {
        // Try to find English voice
        const englishVoice = availableVoices.find(voice => voice.lang.startsWith('en'));
        setSelectedVoice(englishVoice || availableVoices[0]);
      }
    };

    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;
    
    return () => {
      window.speechSynthesis.onvoiceschanged = null;
    };
  }, [selectedVoice]);

  const speak = useCallback((text) => {
    if (!text || text.trim().length === 0) {
      console.warn('No text provided to speak');
      return;
    }

    const synth = window.speechSynthesis;
    
    if (!synth) {
      console.error('Speech synthesis not supported');
      return;
    }
    
    // Cancel any ongoing speech
    synth.cancel();
    
    console.log('Starting to speak:', text.substring(0, 50) + '...');
    
    const utterance = new SpeechSynthesisUtterance(text);
    
    if (selectedVoice) {
      utterance.voice = selectedVoice;
      console.log('Using voice:', selectedVoice.name);
    }
    
    utterance.pitch = 1;
    utterance.rate = 0.95; // Slightly slower for clarity
    utterance.volume = 1;

    utterance.onstart = () => {
      console.log('Speech started');
      setIsSpeaking(true);
    };
    
    utterance.onend = () => {
      console.log('Speech ended');
      setIsSpeaking(false);
    };
    
    utterance.onerror = (event) => {
      console.error('Speech synthesis error:', event.error);
      setIsSpeaking(false);
    };

    synth.speak(utterance);
  }, [selectedVoice]);

  const stop = useCallback(() => {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
  }, []);

  return {
    isSpeaking,
    voices,
    selectedVoice,
    setSelectedVoice,
    speak,
    stop
  };
};
