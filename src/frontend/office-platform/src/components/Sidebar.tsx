import { Link, useLocation } from 'react-router-dom';
import {
  HomeIcon,
  ClipboardDocumentListIcon,
  UserGroupIcon,
  WrenchScrewdriverIcon,
  BellIcon,
} from '@heroicons/react/24/outline';

const navigation = [
  { name: 'Dashboard', icon: HomeIcon, href: '/', notifications: 0 },
  { name: 'Work Orders', icon: ClipboardDocumentListIcon, href: '/work-orders', notifications: 0 },
  { name: 'Technicians', icon: UserGroupIcon, href: '/technicians', notifications: 0 },
  { name: 'Equipment', icon: WrenchScrewdriverIcon, href: '/equipment', notifications: 0 },
];

export default function Sidebar() {
  const location = useLocation();

  return (
    <div className="flex h-screen flex-col justify-between border-r bg-white">
      <div className="px-4 py-6">
        <div className="flex items-center gap-2">
          <img
            src="/logo.svg"
            alt="Company Logo"
            className="h-10 w-10"
          />
          <span className="text-xl font-bold text-gray-900">
            Tech Office
          </span>
        </div>

        <nav className="mt-6 flex flex-1 flex-col">
          <ul role="list" className="space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <li key={item.name}>
                  <Link
                    to={item.href}
                    className={`group relative flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium hover:bg-gray-50 ${
                      isActive ? 'text-primary-600 bg-primary-50' : 'text-gray-700'
                    }`}
                  >
                    <item.icon className="h-5 w-5 flex-shrink-0" />
                    {item.name}
                    {item.notifications > 0 && (
                      <span className="absolute right-0 top-1/2 -translate-y-1/2 mr-2 flex h-5 w-5 items-center justify-center rounded-full bg-primary-100 text-xs font-medium text-primary-600">
                        {item.notifications}
                      </span>
                    )}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </div>

      <div className="sticky inset-x-0 bottom-0 border-t border-gray-100 bg-white p-4">
        <div className="flex items-center gap-2">
          <img
            className="h-10 w-10 rounded-full"
            src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80"
            alt="User"
          />
          <div>
            <p className="text-sm font-medium text-gray-900">Office Admin</p>
            <p className="text-xs text-gray-500">admin@company.com</p>
          </div>
        </div>
      </div>
    </div>
  );
} 