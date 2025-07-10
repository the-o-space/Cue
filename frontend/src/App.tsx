import { useState } from 'react';

function App() {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [images, setImages] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [showSecret, setShowSecret] = useState(false);
  const [secretKey, setSecretKey] = useState('');

  // Listen for cmd+/ or ctrl+/
  const handleGlobalKeyPress = (e: KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === '/') {
      e.preventDefault();
      setShowSecret(!showSecret);
    }
  };

  // Add global key listener
  useState(() => {
    document.addEventListener('keydown', handleGlobalKeyPress);
    return () => document.removeEventListener('keydown', handleGlobalKeyPress);
  });

  const generateArt = async () => {
    if (!text.trim()) return;

    setLoading(true);
    setError(null);
    setImages([]);
    setSubmitted(true);

    try {
      const body: any = { text };
      // Include secret key if provided
      if (secretKey.trim()) {
        body.secret_key = secretKey;
      }

      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        throw new Error('Failed to generate art');
      }

      const data = await response.json();
      setImages(data.images);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
      setSubmitted(false);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      generateArt();
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-white">
      {/* Floating text field - only show if not submitted */}
      {!submitted && (
        <div className="w-full max-w-2xl px-8">
          <div className="relative">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Give me a cue — thought, feeling, a metaphor ..."
              className="w-full h-24 p-4 text-lg border-2 border-gray-200 rounded-lg resize-none 
                       focus:outline-none focus:border-gray-400 transition-all duration-200
                       shadow-lg hover:shadow-xl"
              disabled={loading}
              autoFocus
              enterKeyHint="send"
            />
            
            {/* Secret dropdown */}
            {showSecret && (
              <div className="absolute top-full mt-2 w-full bg-white border-2 border-gray-200 rounded-lg shadow-xl p-4">
                <div className="flex items-center space-x-2">
                  <input
                    type="password"
                    value={secretKey}
                    onChange={(e) => setSecretKey(e.target.value)}
                    placeholder="Secret key for GitHub push..."
                    className="flex-1 p-2 text-sm border border-gray-200 rounded focus:outline-none focus:border-gray-400"
                  />
                  <button
                    onClick={() => setShowSecret(false)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    ✕
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-2">Images will be pushed to GitHub gallery</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="fixed inset-0 flex items-center justify-center bg-white z-50">
          <div className="w-16 h-16 border-4 border-gray-300 border-t-gray-600 rounded-full animate-spin" />
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="fixed top-8 left-1/2 transform -translate-x-1/2 p-4 bg-red-50 border border-red-200 text-red-700 rounded">
          {error}
        </div>
      )}

      {/* Images display in column */}
      {images.length > 0 && !loading && (
        <div className="w-full max-w-4xl mx-auto p-8 space-y-8">
          {images.map((imageUrl, index) => (
            <div key={index} className="w-full">
              <img 
                src={imageUrl} 
                alt={`Generated art variation ${index + 1}`} 
                className="w-full shadow-xl"
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default App; 