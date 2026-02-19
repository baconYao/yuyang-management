import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

interface LayoutProps {
  children: React.ReactNode;
}

const BILL_SUB_ROUTES = [
  { path: '/bills/draft', label: '未處理的帳單' },
  { path: '/bills/processing', label: '請款中的帳單' },
] as const;

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const isBillsPath = location.pathname.startsWith('/bills');
  const [billsMenuOpen, setBillsMenuOpen] = useState(isBillsPath);

  useEffect(() => {
    if (isBillsPath) setBillsMenuOpen(true);
  }, [isBillsPath]);

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  const isBillsSubActive = (path: string) => isActive(path);

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

          {/* 帳單 (toggle with sub-items) */}
          <div>
            <button
              type="button"
              onClick={() => setBillsMenuOpen((open) => !open)}
              className={`flex w-full items-center justify-between px-6 py-3 text-left text-gray-700 hover:bg-gray-100 transition-colors ${
                isBillsPath ? 'bg-blue-50 border-r-4 border-blue-600 text-blue-600' : ''
              }`}
            >
              <span className="ml-3">帳單</span>
              <svg
                className={`ml-2 h-4 w-4 shrink-0 transition-transform ${billsMenuOpen ? 'rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            {billsMenuOpen && (
              <div className="bg-gray-50/80">
                {BILL_SUB_ROUTES.map(({ path, label }) => (
                  <Link
                    key={path}
                    to={path}
                    className={`flex items-center py-2.5 pl-10 pr-6 text-sm text-gray-600 hover:bg-gray-100 hover:text-gray-900 transition-colors ${
                      isBillsSubActive(path) ? 'bg-blue-50 border-r-4 border-blue-600 text-blue-600 font-medium' : ''
                    }`}
                  >
                    {label}
                  </Link>
                ))}
              </div>
            )}
          </div>
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
