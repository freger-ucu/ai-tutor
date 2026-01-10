# AI Tutor Frontend

React + TypeScript + Vite frontend for the AI Tutor system.

## Setup

```bash
# Install dependencies
npm install

# Run development server
npm run dev
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Project Structure

```
frontend/
├── src/
│   ├── api/          # API client
│   ├── components/   # React components
│   ├── pages/        # Page components
│   └── types/        # TypeScript types
├── public/           # Static assets
└── index.html        # Entry point
```

## Environment Variables

Create `.env.local` with:

```
VITE_API_URL=http://localhost:8000
```
