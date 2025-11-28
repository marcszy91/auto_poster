import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { userApi, type UserCredentials, type UserCredentialsResponse } from "../services/api";
import { useAuthStore } from "../store/authStore";

export default function UserSettingsPage() {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [credentials, setCredentials] = useState<UserCredentialsResponse | null>(null);

  // Form state
  const [instagramUsername, setInstagramUsername] = useState("");
  const [instagramPassword, setInstagramPassword] = useState("");
  const [youtubeClientId, setYoutubeClientId] = useState("");
  const [youtubeClientSecret, setYoutubeClientSecret] = useState("");
  const [youtubeRefreshToken, setYoutubeRefreshToken] = useState("");
  const [groqApiKey, setGroqApiKey] = useState("");

  // Password change state
  const [showPasswordChange, setShowPasswordChange] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");

  useEffect(() => {
    loadCredentials();
  }, []);

  const loadCredentials = async () => {
    try {
      setIsLoading(true);
      const data = await userApi.getCredentials();
      setCredentials(data);

      // Set Instagram username if available
      if (data.instagram_username) {
        setInstagramUsername(data.instagram_username);
      }
    } catch (error) {
      console.error("Failed to load credentials:", error);
      toast.error("Failed to load settings");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveCredentials = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);

    try {
      const updates: UserCredentials = {};

      // Only include fields that have been modified
      if (instagramUsername) updates.instagram_username = instagramUsername;
      if (instagramPassword) updates.instagram_password = instagramPassword;
      if (youtubeClientId) updates.youtube_client_id = youtubeClientId;
      if (youtubeClientSecret) updates.youtube_client_secret = youtubeClientSecret;
      if (youtubeRefreshToken) updates.youtube_refresh_token = youtubeRefreshToken;
      if (groqApiKey) updates.groq_api_key = groqApiKey;

      await userApi.updateCredentials(updates);
      toast.success("Credentials saved successfully!");

      // Clear password fields
      setInstagramPassword("");
      setYoutubeClientSecret("");
      setYoutubeRefreshToken("");
      setGroqApiKey("");

      // Reload to show updated status
      await loadCredentials();
    } catch (error: any) {
      console.error("Save error:", error);
      toast.error(error.response?.data?.detail || "Failed to save credentials");
    } finally {
      setIsSaving(false);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();

    if (newPassword !== confirmNewPassword) {
      toast.error("New passwords do not match");
      return;
    }

    if (newPassword.length < 8) {
      toast.error("Password must be at least 8 characters");
      return;
    }

    try {
      await userApi.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });

      toast.success("Password changed successfully!");
      setShowPasswordChange(false);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmNewPassword("");
    } catch (error: any) {
      console.error("Password change error:", error);
      toast.error(error.response?.data?.detail || "Failed to change password");
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600">Loading settings...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
              <p className="mt-1 text-sm text-gray-600">
                Manage your account and platform credentials
              </p>
            </div>
            <button
              onClick={() => navigate("/")}
              className="text-gray-600 hover:text-gray-900"
            >
              ← Back to Home
            </button>
          </div>
        </div>

        {/* User Info */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Account</h2>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Email:</span>
              <span className="font-medium">{user?.email}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Email Verified:</span>
              <span className={user?.is_verified ? "text-green-600" : "text-orange-600"}>
                {user?.is_verified ? "✓ Verified" : "⚠ Not Verified"}
              </span>
            </div>
            {!user?.is_verified && (
              <p className="text-xs text-orange-600 mt-2">
                Please check your email to verify your account
              </p>
            )}
          </div>

          {/* Password Change */}
          <div className="mt-6 pt-6 border-t">
            <button
              onClick={() => setShowPasswordChange(!showPasswordChange)}
              className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
            >
              {showPasswordChange ? "Cancel" : "Change Password"}
            </button>

            {showPasswordChange && (
              <form onSubmit={handlePasswordChange} className="mt-4 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Current Password
                  </label>
                  <input
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    required
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    New Password
                  </label>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Confirm New Password
                  </label>
                  <input
                    type="password"
                    value={confirmNewPassword}
                    onChange={(e) => setConfirmNewPassword(e.target.value)}
                    required
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 text-sm font-medium"
                >
                  Update Password
                </button>
              </form>
            )}
          </div>
        </div>

        {/* Platform Credentials */}
        <form onSubmit={handleSaveCredentials}>
          {/* Instagram */}
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Instagram Credentials
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Username
                </label>
                <input
                  type="text"
                  value={instagramUsername}
                  onChange={(e) => setInstagramUsername(e.target.value)}
                  placeholder="your_instagram_username"
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Password
                  {credentials?.instagram_password_set && (
                    <span className="ml-2 text-xs text-green-600">✓ Set</span>
                  )}
                </label>
                <input
                  type="password"
                  value={instagramPassword}
                  onChange={(e) => setInstagramPassword(e.target.value)}
                  placeholder={credentials?.instagram_password_set ? "••••••••" : "Enter password"}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Leave empty to keep current password
                </p>
              </div>
            </div>
          </div>

          {/* YouTube */}
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              YouTube Credentials
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Client ID
                  {credentials?.youtube_client_id_set && (
                    <span className="ml-2 text-xs text-green-600">✓ Set</span>
                  )}
                </label>
                <input
                  type="text"
                  value={youtubeClientId}
                  onChange={(e) => setYoutubeClientId(e.target.value)}
                  placeholder="your_client_id.apps.googleusercontent.com"
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Client Secret
                  {credentials?.youtube_client_secret_set && (
                    <span className="ml-2 text-xs text-green-600">✓ Set</span>
                  )}
                </label>
                <input
                  type="password"
                  value={youtubeClientSecret}
                  onChange={(e) => setYoutubeClientSecret(e.target.value)}
                  placeholder={credentials?.youtube_client_secret_set ? "••••••••" : "Enter client secret"}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Refresh Token
                  {credentials?.youtube_refresh_token_set && (
                    <span className="ml-2 text-xs text-green-600">✓ Set</span>
                  )}
                </label>
                <input
                  type="password"
                  value={youtubeRefreshToken}
                  onChange={(e) => setYoutubeRefreshToken(e.target.value)}
                  placeholder={credentials?.youtube_refresh_token_set ? "••••••••" : "Enter refresh token"}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
            </div>
          </div>

          {/* Groq */}
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Groq API Key
            </h2>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                API Key
                {credentials?.groq_api_key_set && (
                  <span className="ml-2 text-xs text-green-600">✓ Set</span>
                )}
              </label>
              <input
                type="password"
                value={groqApiKey}
                onChange={(e) => setGroqApiKey(e.target.value)}
                placeholder={credentials?.groq_api_key_set ? "••••••••" : "Enter API key"}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              />
              <p className="mt-1 text-xs text-gray-500">
                Used for AI text generation
              </p>
            </div>
          </div>

          {/* Save Button */}
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={isSaving}
              className="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSaving ? "Saving..." : "Save Credentials"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
