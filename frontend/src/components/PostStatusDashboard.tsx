import React, { useEffect, useState } from "react";
import { getPosts } from "../services/api";
import type { Post } from "../types/post";

const getStatusColor = (status: string) => {
  switch (status) {
    case "success":
      return "bg-green-100 text-green-800";
    case "failed":
      return "bg-red-100 text-red-800";
    case "processing":
      return "bg-yellow-100 text-yellow-800";
    case "pending":
      return "bg-gray-100 text-gray-800";
    case "skipped":
      return "bg-blue-100 text-blue-800";
    default:
      return "bg-gray-100 text-gray-800";
  }
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case "success":
      return (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
            clipRule="evenodd"
          />
        </svg>
      );
    case "failed":
      return (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
            clipRule="evenodd"
          />
        </svg>
      );
    case "processing":
      return (
        <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
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
      );
    default:
      return (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z"
            clipRule="evenodd"
          />
        </svg>
      );
  }
};

export const PostStatusDashboard: React.FC = () => {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPosts = async () => {
    try {
      const response = await getPosts(1, 50);
      setPosts(response.posts);
      setError(null);
    } catch (err) {
      setError("Failed to fetch posts");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Only fetch posts on initial load
    fetchPosts();

    // Auto-refresh disabled - use manual refresh button instead
    // const interval = setInterval(fetchPosts, 5000);
    // setRefreshInterval(interval);

    // return () => {
    //   if (interval) clearInterval(interval);
    // };
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        {error}
      </div>
    );
  }

  if (posts.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>No posts yet. Create your first post above!</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold text-gray-900">Post History</h2>
        <button
          onClick={fetchPosts}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          Refresh
        </button>
      </div>

      <div className="grid gap-4">
        {posts.map((post) => (
          <div
            key={post.id}
            className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
          >
            <div className="flex flex-col md:flex-row gap-6">
              {/* Image */}
              <div className="flex-shrink-0">
                <img
                  src={`/${post.main_image_path}`}
                  alt={post.title || "Post image"}
                  className="w-32 h-32 object-cover rounded-lg"
                  onError={(e) => {
                    // Fallback to icon if image fails to load
                    const target = e.currentTarget;
                    target.style.display = "none";
                    const parent = target.parentElement;
                    if (parent) {
                      parent.innerHTML = `
                        <div class="w-32 h-32 bg-gray-200 rounded-lg flex items-center justify-center">
                          <svg class="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                        </div>
                      `;
                    }
                  }}
                />
              </div>

              {/* Content */}
              <div className="flex-grow">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {post.title || "Untitled"}
                </h3>
                <p className="text-sm text-gray-600 mb-3">
                  Designer: {post.designer_name || "Unknown"}
                </p>
                <div className="flex flex-wrap gap-2 mb-4">
                  {post.print_duration && (
                    <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                      {post.print_duration}
                    </span>
                  )}
                  {post.material && (
                    <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                      {post.material}
                    </span>
                  )}
                  {post.material_amount && (
                    <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                      {post.material_amount}
                    </span>
                  )}
                </div>

                {/* Platform Status */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {/* Instagram */}
                  <div
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg ${getStatusColor(
                      post.instagram.status,
                    )}`}
                  >
                    {getStatusIcon(post.instagram.status)}
                    <div className="flex-grow">
                      <div className="font-medium text-sm">Instagram</div>
                      <div className="text-xs capitalize">
                        {post.instagram.status}
                      </div>
                    </div>
                  </div>

                  {/* YouTube */}
                  <div
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg ${getStatusColor(
                      post.youtube.status,
                    )}`}
                  >
                    {getStatusIcon(post.youtube.status)}
                    <div className="flex-grow">
                      <div className="font-medium text-sm">YouTube</div>
                      <div className="text-xs capitalize">
                        {post.youtube.status}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Error Messages */}
                {(post.instagram.error || post.youtube.error) && (
                  <div className="mt-3 space-y-1">
                    {post.instagram.error && (
                      <p className="text-xs text-red-600">
                        Instagram: {post.instagram.error}
                      </p>
                    )}
                    {post.youtube.error && (
                      <p className="text-xs text-red-600">
                        YouTube: {post.youtube.error}
                      </p>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Footer */}
            <div className="mt-4 pt-4 border-t border-gray-200">
              <p className="text-xs text-gray-500">
                Created: {new Date(post.created_at).toLocaleString()}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
