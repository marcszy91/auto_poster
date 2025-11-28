import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
import toast from "react-hot-toast";

const logoSrc = "/auto-poster.svg";

export default function Navigation() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onClickAway = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", onClickAway);
    return () => document.removeEventListener("mousedown", onClickAway);
  }, []);

  const handleLogout = async () => {
    try {
      await logout();
      toast.success("Logged out successfully");
      navigate("/login");
    } catch (error) {
      console.error("Logout error:", error);
      toast.error("Logout failed");
    }
  };

  const handleSettings = () => {
    navigate("/settings");
    setMenuOpen(false);
  };

  const avatarInitial = user?.email?.[0]?.toUpperCase() || "?";

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo/Title */}
          <div className="flex items-center gap-3">
            <img src={logoSrc} alt="Auto Poster logo" className="h-9 w-9" />
            <div className="leading-tight">
              <div className="text-lg font-semibold text-gray-900">
                Auto Poster
              </div>
              <div className="text-xs text-gray-500">
                Automate & schedule content
              </div>
            </div>
          </div>

          {/* User Menu */}
          <div className="flex items-center space-x-4">
            {user && (
              <div className="relative" ref={menuRef}>
                <button
                  onClick={() => setMenuOpen((prev) => !prev)}
                  className="flex items-center justify-center h-10 w-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-white font-semibold shadow-sm hover:shadow transition-transform duration-150 hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  {avatarInitial}
                </button>

                {menuOpen && (
                  <div className="absolute right-0 mt-3 w-56 rounded-lg bg-white shadow-lg border border-gray-100 py-2 z-20">
                    <div className="px-4 py-2">
                      <p className="text-xs text-gray-500">Signed in as</p>
                      <p className="text-sm font-medium text-gray-900 break-all">
                        {user.email}
                      </p>
                      {!user.is_verified && (
                        <p className="mt-1 text-xs text-orange-600">
                          Email not verified
                        </p>
                      )}
                    </div>
                    <div className="border-t border-gray-100 my-2" />
                    <button
                      onClick={handleSettings}
                      className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                    >
                      Settings
                    </button>
                    <button
                      onClick={handleLogout}
                      className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                    >
                      Logout
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
