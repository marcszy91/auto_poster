import React, { useState } from 'react';
import toast, { Toaster } from 'react-hot-toast';
import Navigation from '../components/Navigation';
import { ImageUpload } from '../components/ImageUpload';
import { PostStatusDashboard } from '../components/PostStatusDashboard';
import { createPost, generateText } from '../services/api';

export const HomePage: React.FC = () => {
  const [makerworldId, setMakerworldId] = useState('');
  const [mainImage, setMainImage] = useState<File | null>(null);
  const [additionalImages, setAdditionalImages] = useState<File[]>([]);
  const [keywords, setKeywords] = useState('');
  const [generatedText, setGeneratedText] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [refreshDashboard, setRefreshDashboard] = useState(0);

  // Platform selections (all enabled by default)
  const [postToInstagramFeed, setPostToInstagramFeed] = useState(true);
  const [postToInstagramReel, setPostToInstagramReel] = useState(true);
  const [postToInstagramStory, setPostToInstagramStory] = useState(true);
  const [postToYouTubeShort, setPostToYouTubeShort] = useState(true);

  const handleGenerateText = async () => {
    if (!keywords.trim()) {
      toast.error('Bitte gib zuerst Stichwörter ein');
      return;
    }

    setIsGenerating(true);
    const loadingToast = toast.loading('Text wird generiert...');

    try {
      const text = await generateText(keywords.trim());
      setGeneratedText(text);
      toast.success('Text erfolgreich generiert!', { id: loadingToast });
    } catch (error: any) {
      console.error('Error generating text:', error);
      toast.error(error.response?.data?.detail || 'Textgenerierung fehlgeschlagen', {
        id: loadingToast,
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!makerworldId || !mainImage) {
      toast.error('Please provide a MakerWorld ID and main image');
      return;
    }

    setIsSubmitting(true);
    const loadingToast = toast.loading('Creating post...');

    try {
      const formData = new FormData();
      formData.append('makerworld_id', makerworldId);
      formData.append('main_image', mainImage);

      if (generatedText.trim()) {
        formData.append('generated_text', generatedText.trim());
      }

      // Add platform selections
      formData.append('post_instagram_feed', postToInstagramFeed.toString());
      formData.append('post_instagram_reel', postToInstagramReel.toString());
      formData.append('post_instagram_story', postToInstagramStory.toString());
      formData.append('post_youtube_short', postToYouTubeShort.toString());

      additionalImages.forEach((image) => {
        formData.append('additional_images', image);
      });

      await createPost(formData);

      toast.success('Post created successfully! Processing social media uploads...', {
        id: loadingToast,
        duration: 5000,
      });

      // Reset form
      setMakerworldId('');
      setMainImage(null);
      setAdditionalImages([]);
      setKeywords('');
      setGeneratedText('');

      // Trigger dashboard refresh
      setRefreshDashboard((prev) => prev + 1);
    } catch (error: any) {
      console.error('Error creating post:', error);
      toast.error(error.response?.data?.detail || 'Failed to create post. Please try again.', {
        id: loadingToast,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Toaster position="top-right" />

      {/* Navigation */}
      <Navigation />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Upload Form */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Create New Post</h2>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* MakerWorld ID Input */}
            <div>
              <label
                htmlFor="makerworld-id"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                MakerWorld Model ID or URL <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="makerworld-id"
                value={makerworldId}
                onChange={(e) => setMakerworldId(e.target.value)}
                placeholder="e.g., 938881 or https://makerworld.com/de/models/938881#profileId-904221"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors"
                required
              />
              <p className="mt-1 text-sm text-gray-500">
                Enter either the model ID (e.g., 938881) or the full URL with profile ID to fetch
                specific print settings
              </p>
            </div>

            {/* Image Upload */}
            <ImageUpload
              mainImage={mainImage}
              additionalImages={additionalImages}
              onMainImageChange={setMainImage}
              onAdditionalImagesChange={setAdditionalImages}
            />

            {/* Platform Selection */}
            <div className="border-t pt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Plattformen auswählen</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Instagram Feed */}
                <div className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="flex-grow">
                    <div className="font-medium text-gray-900">Instagram Feed Post</div>
                    <div className="text-sm text-gray-500">Foto im normalen Feed</div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setPostToInstagramFeed(!postToInstagramFeed)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
                      postToInstagramFeed ? 'bg-primary-600' : 'bg-gray-200'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        postToInstagramFeed ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                {/* Instagram Reel */}
                <div className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="flex-grow">
                    <div className="font-medium text-gray-900">Instagram Reel</div>
                    <div className="text-sm text-gray-500">Video mit Template + Musik</div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setPostToInstagramReel(!postToInstagramReel)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
                      postToInstagramReel ? 'bg-primary-600' : 'bg-gray-200'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        postToInstagramReel ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                {/* Instagram Story */}
                <div className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="flex-grow">
                    <div className="font-medium text-gray-900">Instagram Story</div>
                    <div className="text-sm text-gray-500">Video Story (24h)</div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setPostToInstagramStory(!postToInstagramStory)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
                      postToInstagramStory ? 'bg-primary-600' : 'bg-gray-200'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        postToInstagramStory ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                {/* YouTube Short */}
                <div className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="flex-grow">
                    <div className="font-medium text-gray-900">YouTube Short</div>
                    <div className="text-sm text-gray-500">Kurzvideo auf YouTube</div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setPostToYouTubeShort(!postToYouTubeShort)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
                      postToYouTubeShort ? 'bg-primary-600' : 'bg-gray-200'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        postToYouTubeShort ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              </div>
            </div>

            {/* AI Text Generation Section */}
            <div className="space-y-4 border-t pt-6">
              <h3 className="text-lg font-semibold text-gray-900">AI Textgenerierung (Optional)</h3>

              {/* Keywords Input */}
              <div>
                <label htmlFor="keywords" className="block text-sm font-medium text-gray-700 mb-2">
                  Stichwörter (Deutsch)
                </label>
                <div className="flex gap-2">
                  <textarea
                    id="keywords"
                    value={keywords}
                    onChange={(e) => setKeywords(e.target.value)}
                    placeholder="z.B. Weihnachtsdeko, minimalistisches Design, skandinavischer Stil"
                    rows={2}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors resize-none"
                  />
                  <button
                    type="button"
                    onClick={handleGenerateText}
                    disabled={isGenerating || !keywords.trim()}
                    className="px-4 py-2 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors whitespace-nowrap self-start"
                  >
                    {isGenerating ? (
                      <span className="flex items-center">
                        <svg
                          className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                        >
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                          ></circle>
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                          ></path>
                        </svg>
                        Generiere...
                      </span>
                    ) : (
                      'Text generieren'
                    )}
                  </button>
                </div>
                <p className="mt-1 text-sm text-gray-500">
                  Gib deutsche Stichwörter ein und klicke auf "Text generieren" für eine englische
                  Beschreibung
                </p>
              </div>

              {/* Generated Text Display/Edit */}
              <div>
                <label
                  htmlFor="generated-text"
                  className="block text-sm font-medium text-gray-700 mb-2"
                >
                  Generierter Text (Englisch) - Bearbeitbar
                </label>
                <textarea
                  id="generated-text"
                  value={generatedText}
                  onChange={(e) => setGeneratedText(e.target.value)}
                  placeholder="Hier erscheint der generierte Text, den du noch bearbeiten kannst..."
                  rows={4}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors resize-none"
                />
                <p className="mt-1 text-sm text-gray-500">
                  Du kannst den generierten Text bearbeiten oder eigenen Text eingeben. Leer lassen
                  um zu überspringen.
                </p>
              </div>
            </div>

            {/* Submit Button */}
            <div className="flex justify-end pt-4">
              <button
                type="submit"
                disabled={isSubmitting || !makerworldId || !mainImage}
                className="px-6 py-3 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isSubmitting ? (
                  <span className="flex items-center">
                    <svg
                      className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    Creating Post...
                  </span>
                ) : (
                  'Create Post'
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Post Status Dashboard */}
        <PostStatusDashboard key={refreshDashboard} />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            Auto Poster - Automated Social Media Management
          </p>
        </div>
      </footer>
    </div>
  );
};
