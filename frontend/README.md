# SQL Dashboard Frontend

Frontend application for the SQL Dashboard, built with React, TypeScript, and Vite.

## Features

- React 18+ with TypeScript
- Vite for fast development and building
- TanStack Query (React Query) for server state management
- Axios for HTTP requests
- React Router for URL state management
- Fast refresh and hot module replacement (HMR)

## Requirements

- Node.js 20+
- npm 10+

## Setup Instructions

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

The frontend is configured to proxy `/api` requests to the backend at `http://localhost:8000`.
This is configured in `vite.config.ts`.

### 3. Run the Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:5173`.

## Available Scripts

- `npm run dev` - Start development server with hot reload
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint

## Project Structure

```
frontend/
├── src/
│   ├── lib/
│   │   └── api.ts              # API client configuration
│   ├── components/             # React components (to be added)
│   ├── hooks/                  # Custom hooks (to be added)
│   ├── types.ts                # TypeScript type definitions
│   ├── App.tsx                 # Main application component
│   ├── App.css                 # Application styles
│   ├── main.tsx                # Application entry point
│   └── index.css               # Global styles
├── public/                     # Static assets
├── index.html                  # HTML template
├── vite.config.ts              # Vite configuration
├── tsconfig.json               # TypeScript configuration
├── package.json                # Project dependencies
└── README.md                   # This file
```

## Development

### API Communication

The frontend communicates with the backend API through the axios client configured in `src/lib/api.ts`.
All API requests are automatically proxied to the backend server.

Example:
```typescript
import { checkHealth } from './lib/api';

// This will make a request to http://localhost:8000/api/health
const health = await checkHealth();
```

### Adding New API Endpoints

1. Add the function to `src/lib/api.ts`
2. Define the response types
3. Use React Query hooks to call the API

Example:
```typescript
// In api.ts
export const getSchema = async () => {
  const response = await api.get('/schema');
  return response.data;
};

// In a component
import { useQuery } from '@tanstack/react-query';
import { getSchema } from './lib/api';

function MyComponent() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['schema'],
    queryFn: getSchema,
  });

  // ... render component
}
```

### Type Definitions

All TypeScript types should be defined in `src/types.ts` or in dedicated type files
for better organization as the project grows.

## Next Steps

- [ ] Implement dashboard layout with grid system
- [ ] Add table display components
- [ ] Create filter builder UI
- [ ] Implement URL state management
- [ ] Add file upload component
- [ ] Create comprehensive component tests

## Testing

Testing infrastructure will be added in later phases using:
- Vitest for unit tests
- React Testing Library for component tests
- Playwright/Cypress for E2E tests

## License

See the main project README for license information.
