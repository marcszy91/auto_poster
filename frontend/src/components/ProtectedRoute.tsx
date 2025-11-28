import { useEffect } from "react";
import { Navigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireVerified?: boolean;
}

export default function ProtectedRoute({
  children,
  requireVerified = false,
}: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user, checkAuth } = useAuthStore();

  // Check auth on mount
  useEffect(() => {
    if (!isAuthenticated && !isLoading) {
      checkAuth();
    }
  }, [isAuthenticated, isLoading, checkAuth]);

  // Show loading while checking auth
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600">Loading...</div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Check if email verification is required
  if (requireVerified && user && !user.is_verified) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-sm p-8 text-center">
          <div className="text-orange-500 text-5xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Email Verification Required
          </h2>
          <p className="text-gray-600 mb-6">
            Please verify your email address to access this feature. Check your
            inbox for a verification link.
          </p>
          <p className="text-sm text-gray-500">
            Email sent to: <span className="font-medium">{user.email}</span>
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
