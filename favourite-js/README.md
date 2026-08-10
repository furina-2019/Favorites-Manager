# Favourite - JavaScript Version

A modern favorites manager built with React, TypeScript, and Vite.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- npm 9+

### Installation

```bash
# Navigate to project directory
cd favourite-js

# Install dependencies
npm install
```

### Development

```bash
# Start development server
npm run dev

# The app will be available at http://localhost:5173
```

### Build

```bash
# Production build
npm run build

# Preview production build
npm run preview
```

## 📁 Project Structure

```
favourite-js/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── Layout.tsx       # Main layout with header/footer
│   │   ├── FolderCard.tsx   # Folder card component
│   │   ├── FolderDialog.tsx # Add/Edit folder dialog
│   │   ├── ItemCard.tsx     # Item card component
│   │   └── ItemDialog.tsx   # Add/Edit item dialog
│   ├── pages/               # Page components
│   │   ├── HomePage.tsx     # Folders list page
│   │   ├── ItemsPage.tsx    # Items list page
│   │   ├── SettingsPage.tsx # Settings page
│   │   └── AboutPage.tsx    # About page
│   ├── stores/              # State management (Zustand)
│   │   ├── uiStore.ts       # UI state (theme, language)
│   │   └── dbStore.ts       # Database state and operations
│   ├── core/                # Core business logic
│   │   └── database.ts      # SQLite database operations
│   ├── i18n/                # Internationalization
│   │   ├── index.ts         # i18n setup
│   │   └── locales/         # Translation files
│   │       ├── en.ts        # English translations
│   │       └── zh.ts        # Chinese translations
│   ├── App.tsx              # Root application component
│   ├── main.tsx             # Application entry point
│   └── index.css            # Global styles
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── postcss.config.js
```

## 🛠️ Tech Stack

- **Frontend Framework**: React 18
- **Language**: TypeScript
- **Build Tool**: Vite
- **UI Library**: Ant Design 5
- **State Management**: Zustand
- **Database**: SQLite (via sql.js)
- **Internationalization**: i18next
- **Styling**: Tailwind CSS + Ant Design

## 📱 Features

### Current Features
- ✅ Create, edit, delete folders
- ✅ Add, edit, delete items (links & files)
- ✅ Search and filter items
- ✅ Item categories
- ✅ Dark/Light mode
- ✅ Customizable theme colors
- ✅ Multi-language support (English/Chinese)
- ✅ Responsive design

### Planned Features
- 🔄 Mind map view (using Konva.js)
- 🔄 Data export/import
- 🔄 AI-powered summaries
- 📦 Tauri desktop packaging
- 📱 Capacitor Android/iOS packaging

## 🎨 Screenshots

*(Coming soon)*

## 📝 License

MIT License
