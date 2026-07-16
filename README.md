# Saar AI

> Discover the essence of your data.

Saar AI is an intelligent analytics platform where users can upload datasets, clean and explore data, generate visualizations, build ML models, and interact with an AI assistant — all from a single, clean interface.

**"Saar"** (सार) means *the essence* of something.

---

## Goals

- Make data analytics accessible through a clean, modern interface
- Provide AI-powered insights without requiring coding knowledge
- Support the full data lifecycle: upload → clean → explore → visualize → model → report
- Deliver a premium, distraction-free experience

---

## Tech Stack

### Frontend
- **Next.js** — App Router, TypeScript
- **Tailwind CSS v4** — Utility-first styling
- **shadcn/ui** — UI component primitives
- **Lucide Icons** — Icon system

### Backend (Phase 2+)
- **FastAPI** — Python web framework
- **Pandas / NumPy** — Data processing
- **Scikit-learn** — Machine learning

### AI (Phase 6+)
- **Ollama** — Local LLM
- **Gemini** — Cloud LLM (optional)

---

## Folder Structure

```
src/
├── app/              # Next.js pages and layouts
├── components/
│   ├── layout/       # App shell, navbar, sidebar
│   ├── ui/           # shadcn/ui primitives
│   └── common/       # Shared components
├── features/         # Feature modules (datasets, ML, etc.)
├── hooks/            # Custom React hooks
├── services/         # API clients
├── lib/              # Utilities
├── constants/        # Configuration
├── types/            # TypeScript definitions
└── styles/           # Additional styles

docs/                 # Project documentation
```

---

## Project Roadmap

| Phase | Name | Status |
|---|---|---|
| 1 | Project Foundation | ✅ Complete |
| 2 | Dataset Management | ⬜ Planned |
| 3 | Data Cleaning | ⬜ Planned |
| 4 | Data Visualization | ⬜ Planned |
| 5 | Machine Learning | ⬜ Planned |
| 6 | AI Assistant | ⬜ Planned |
| 7 | Reports | ⬜ Planned |
| 8 | Deployment | ⬜ Planned |

See [docs/ROADMAP.md](docs/ROADMAP.md) for detailed phase descriptions.

---

## Local Setup

### Prerequisites

- Node.js 22+ (install via [nvm](https://github.com/nvm-sh/nvm))

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/saar-ai.git
cd saar-ai

# Install dependencies
npm install

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Available Scripts

| Command | Description |
|---|---|
| `npm run dev` | Start development server |
| `npm run build` | Create production build |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |

---

## Development Workflow

1. Read the [Contributing Guide](docs/CONTRIBUTING.md)
2. Check the [Roadmap](docs/ROADMAP.md) for current phase
3. Create a feature branch: `feat/your-feature`
4. Make changes following [Architecture](docs/ARCHITECTURE.md) conventions
5. Ensure `npm run build` and `npm run lint` pass
6. Submit a pull request

---

## Documentation

| Document | Description |
|---|---|
| [ROADMAP.md](docs/ROADMAP.md) | Development phases and progress |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture and design decisions |
| [DESIGN_SYSTEM.md](docs/DESIGN_SYSTEM.md) | Visual design specifications |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Render and Vercel deployment instructions |
| [CONTRIBUTING.md](docs/CONTRIBUTING.md) | Coding and contribution guidelines |
| [CHANGELOG.md](docs/CHANGELOG.md) | Version history |

---

## Screenshots

*Screenshots will be added after each phase is complete.*

---

## License

*License to be determined.*
