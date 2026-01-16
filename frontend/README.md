# Yuyang Management System - Frontend

This is a CMS management system frontend application built with React + TypeScript + Vite.

## Features

- 📊 **Dashboard**: Displays total customer count, total contract count, and customer type statistics
- 👥 **Customer Management**: Customer list, search, type filtering, and pagination
- 📄 **Contract Management**: Contract list, search, and pagination
- 🎨 **Modern UI**: Beautiful interface built with Tailwind CSS
- 🔐 **Auth Ready**: Pre-configured authentication extension interface

## Tech Stack

- React 18
- TypeScript
- Vite
- React Router
- Axios
- Tailwind CSS

## Development

### Install Dependencies

```bash
npm install
```

### Start Development Server

```bash
npm run dev
```

The application will run at `http://localhost:3000`.

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/      # React components
│   │   └── Layout.tsx   # Main layout component (includes navigation bar)
│   ├── pages/           # Page components
│   │   ├── Dashboard.tsx
│   │   ├── Customers.tsx
│   │   └── Contracts.tsx
│   ├── services/        # API services
│   │   └── api.ts       # API call functions
│   ├── types/           # TypeScript type definitions
│   │   └── index.ts
│   ├── utils/           # Utility functions
│   │   └── customerTypeLabels.ts
│   ├── App.tsx          # Main application component
│   ├── main.tsx         # Application entry point
│   └── index.css        # Global styles
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## API Configuration

The frontend connects to the backend API through a proxy. The proxy is configured in `vite.config.ts`:

```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
}
```

Ensure the backend service is running on `http://localhost:8000`.

## Future Extensions

### Authentication

The authentication token interceptor code is already prepared in `src/services/api.ts` (commented out). When implementing authentication, simply:

1. Uncomment the `api.interceptors.request.use` section
2. Implement login page and authentication logic
3. Store the token in `localStorage` after successful login

### Other Features

- Create, edit, and delete functionality for customers and contracts
- More detailed data display
- Data export functionality
- Advanced search and filtering
