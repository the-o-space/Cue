import { useState } from 'react';

function App() {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [sentiment, setSentiment] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const generateArt = async () => {
    if (!text.trim()) return;

    setLoading(true);
    setError(null);
    setImageUrl(null);
    setSentiment(null);

    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate art');
      }

      const data = await response.json();
      setImageUrl(data.image_url);
      setSentiment(data.sentiment_scores);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-8 max-w-4xl mx-auto">
      <header className="mb-12">
        <h1 className="text-2xl font-normal mb-2">Cue</h1>
        <p className="text-gray-600">Transform text into abstract art through sentiment analysis</p>
      </header>

      <main className="space-y-8">
        {/* Input Section */}
        <div className="space-y-4">
          <label htmlFor="text-input" className="block text-sm text-gray-700">
            Enter your text
          </label>
          <textarea
            id="text-input"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Type anything — a thought, feeling, or description..."
            className="w-full h-32 p-4 border border-gray-300 rounded-none resize-none focus:outline-none focus:ring-2 focus:ring-black focus:ring-offset-2"
            disabled={loading}
          />
          <button
            onClick={generateArt}
            disabled={loading || !text.trim()}
            className="px-6 py-2 bg-black text-white disabled:bg-gray-400 hover:bg-gray-800 transition-colors"
          >
            {loading ? 'Generating...' : 'Generate Art'}
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 text-red-700">
            {error}
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="space-y-4">
            <div className="h-96 bg-gray-100 loading-pulse" />
            <p className="text-gray-600 text-center">Analyzing sentiment and creating art...</p>
          </div>
        )}

        {/* Result Display */}
        {imageUrl && sentiment && !loading && (
          <div className="space-y-6">
            {/* Generated Image */}
            <div className="border border-gray-200">
              <img 
                src={imageUrl} 
                alt="Generated art" 
                className="w-full"
              />
            </div>

            {/* Sentiment Scores */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 py-4 border-t border-gray-200">
              <div>
                <div className="text-2xl font-light">{Math.round(sentiment.positiveness * 100)}%</div>
                <div className="text-sm text-gray-600">Positiveness</div>
              </div>
              <div>
                <div className="text-2xl font-light">{Math.round(sentiment.energy * 100)}%</div>
                <div className="text-sm text-gray-600">Energy</div>
              </div>
              <div>
                <div className="text-2xl font-light">{Math.round(sentiment.complexity * 100)}%</div>
                <div className="text-sm text-gray-600">Complexity</div>
              </div>
              <div>
                <div className="text-2xl font-light">{Math.round(sentiment.conflictness * 100)}%</div>
                <div className="text-sm text-gray-600">Conflictness</div>
              </div>
            </div>

            {/* Try Again */}
            <button
              onClick={() => {
                setText('');
                setImageUrl(null);
                setSentiment(null);
              }}
              className="text-gray-600 hover:text-black underline"
            >
              Try another text
            </button>
          </div>
        )}
      </main>

      <footer className="mt-16 py-8 border-t border-gray-200 text-sm text-gray-600">
        <p>Powered by Claude AI and generative algorithms</p>
      </footer>
    </div>
  );
}

export default App; 