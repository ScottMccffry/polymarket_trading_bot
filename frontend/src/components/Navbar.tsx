"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

const navItems = [
  { name: "Dashboard", href: "/" },
  { name: "Statistics", href: "/statistics" },
  { name: "Messages", href: "/messages" },
  { name: "Markets", href: "/markets" },
  { name: "Settings", href: "/settings" },
];

export default function Navbar() {
  const pathname = usePathname();
  const { user, isLoading, logout } = useAuth();

  return (
    <nav className="bg-gray-900 border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <Link href="/" className="text-xl font-bold text-white">
              Doudinski Investment Fund
            </Link>
          </div>
          <div className="flex items-center space-x-4">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-gray-800 text-white"
                      : "text-gray-300 hover:bg-gray-700 hover:text-white"
                  }`}
                >
                  {item.name}
                </Link>
              );
            })}

            <div className="ml-4 pl-4 border-l border-gray-700">
              {isLoading ? (
                <div className="text-gray-400 text-sm">Loading...</div>
              ) : user ? (
                <div className="flex items-center space-x-3">
                  <span className="text-gray-300 text-sm">{user.email}</span>
                  <button
                    onClick={logout}
                    className="bg-red-600 hover:bg-red-700 text-white text-sm font-medium px-3 py-2 rounded-md transition-colors"
                  >
                    Logout
                  </button>
                </div>
              ) : (
                <Link
                  href="/login"
                  className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-3 py-2 rounded-md transition-colors"
                >
                  Login
                </Link>
              )}
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}
