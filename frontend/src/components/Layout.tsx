import { Link, useLocation } from 'react-router-dom';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Navigation Bar */}
      <aside className="w-64 bg-white shadow-lg">
        <div className="p-6">
          <h1 className="text-2xl font-bold text-gray-800">宇陽管理系統</h1>
        </div>
        <nav className="mt-8">
          <Link
            to="/"
            className={`flex items-center px-6 py-3 text-gray-700 hover:bg-gray-100 transition-colors ${
              isActive('/') ? 'bg-blue-50 border-r-4 border-blue-600 text-blue-600' : ''
            }`}
          >
            <span className="ml-3">儀表板</span>
          </Link>
          <Link
            to="/customers"
            className={`flex items-center px-6 py-3 text-gray-700 hover:bg-gray-100 transition-colors ${
              isActive('/customers') ? 'bg-blue-50 border-r-4 border-blue-600 text-blue-600' : ''
            }`}
          >
            <span className="ml-3">客戶</span>
          </Link>
          <Link
            to="/contracts"
            className={`flex items-center px-6 py-3 text-gray-700 hover:bg-gray-100 transition-colors ${
              isActive('/contracts') ? 'bg-blue-50 border-r-4 border-blue-600 text-blue-600' : ''
            }`}
          >
            <span className="ml-3">合約</span>
          </Link>
          {/* Future: Add user menu and logout functionality here */}
          {/* <div className="absolute bottom-0 w-64 p-4 border-t">
            <button className="w-full text-left px-4 py-2 text-gray-700 hover:bg-gray-100">
              登出
            </button>
          </div> */}
        </nav>
      </aside>

      {/* Right Content Area */}
      <main className="flex-1 overflow-y-auto">
        <div className="p-8">{children}</div>
      </main>
    </div>
  );
}
