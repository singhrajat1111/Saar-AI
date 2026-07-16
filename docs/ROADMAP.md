# Saar AI — Project Roadmap

> **"Saar"** means the essence of something. This platform helps users discover the essence of their datasets.

---

## Phase 1 — Project Foundation

**Objective:** Set up the project infrastructure, architecture, theme, layout shell, and documentation.

**Features:**
- Next.js project initialization with TypeScript and Tailwind CSS v4
- Feature-oriented folder structure
- Google Colab-inspired dark theme
- App shell with sidebar navigation and top navbar
- Dashboard landing page with empty state
- Project documentation

**Deliverables:**
- Compiling Next.js application
- Sidebar with navigation items (disabled for future phases)
- Responsive layout (collapsed sidebar on mobile)
- Complete documentation suite

**Technologies:**
- Next.js 16 (App Router)
- TypeScript
- Tailwind CSS v4
- shadcn/ui
- Lucide Icons

**Folder Changes:**
- `src/app/` — root layout, globals.css, dashboard page
- `src/components/layout/` — app-shell, navbar, sidebar
- `src/components/ui/` — shadcn button, separator, tooltip
- `src/constants/` — navigation config
- `src/lib/` — utils (cn)
- `docs/` — project documentation

**Completion Checklist:**
- [x] Next.js initialized with TypeScript, Tailwind CSS v4, App Router
- [x] Boilerplate cleaned
- [x] shadcn/ui initialized
- [x] Folder structure created
- [x] Dark theme implemented
- [x] Sidebar component
- [x] Navbar component
- [x] App shell component
- [x] Dashboard page
- [x] ROADMAP.md
- [x] ARCHITECTURE.md
- [x] DESIGN_SYSTEM.md
- [x] CONTRIBUTING.md
- [x] CHANGELOG.md
- [x] README.md
- [ ] Build passes
- [ ] Lint passes

---

## Phase 2 — Dataset Management

**Objective:** Allow users to upload, preview, and manage CSV datasets.

**Features:**
- CSV file upload with drag-and-drop
- File validation (type, size, encoding)
- Dataset list view
- Dataset preview (table view)
- Metadata display (rows, columns, types)
- Basic statistics (mean, median, mode, nulls)

**Deliverables:**
- Upload component with validation
- Dataset list page
- Dataset detail/preview page
- FastAPI backend for file handling
- Dataset storage and retrieval

**Technologies:**
- FastAPI, Python, Pandas
- TanStack Query (frontend data fetching)
- File upload APIs

**Folder Changes:**
- `src/features/datasets/` — components, hooks, services
- `backend/` — FastAPI application
- `backend/services/` — dataset processing

**Completion Checklist:**
- [ ] CSV upload with validation
- [ ] Dataset list view
- [ ] Dataset preview table
- [ ] Metadata display
- [ ] Basic statistics
- [ ] Backend API endpoints
- [ ] Error handling
- [ ] Build passes
- [ ] Lint passes

---

## Phase 3 — Data Cleaning

**Objective:** Provide tools for data cleaning and preparation.

**Features:**
- Missing value detection and handling
- Duplicate row detection and removal
- Datatype inspection and conversion
- AI-powered cleaning suggestions
- Cleaning operation history

**Deliverables:**
- Data quality overview dashboard
- Cleaning operation interface
- Cleaning pipeline execution
- Operation log

**Technologies:**
- Pandas (backend processing)
- Scikit-learn (imputation)

**Folder Changes:**
- `src/features/cleaning/` — components, services
- `backend/services/cleaning/` — cleaning operations

**Completion Checklist:**
- [ ] Missing value detection
- [ ] Duplicate detection
- [ ] Datatype inspection
- [ ] Cleaning operations
- [ ] Operation history
- [ ] Build passes
- [ ] Lint passes

---

## Phase 4 — Data Visualization

**Objective:** Enable interactive data visualization and exploration.

**Features:**
- Bar charts, line charts, scatter plots, histograms
- Configurable axes and parameters
- Interactive filters
- Dashboard widgets
- Export charts as images

**Deliverables:**
- Chart builder interface
- Multiple chart types
- Interactive filtering
- Visualization dashboard

**Technologies:**
- Recharts
- D3.js (if needed)

**Folder Changes:**
- `src/features/visualization/` — components, hooks
- Chart component library

**Completion Checklist:**
- [ ] Chart type selection
- [ ] Configurable chart parameters
- [ ] Interactive filters
- [ ] Dashboard widgets
- [ ] Chart export
- [ ] Build passes
- [ ] Lint passes

---

## Phase 5 — Machine Learning

**Objective:** Provide automated ML model building and evaluation.

**Features:**
- Regression models
- Classification models
- Clustering
- Feature importance analysis
- Prediction interface

**Deliverables:**
- Model builder interface
- Training pipeline
- Results visualization
- Prediction form

**Technologies:**
- Scikit-learn
- NumPy

**Folder Changes:**
- `src/features/ml/` — components, services
- `backend/services/ml/` — model training, prediction

**Completion Checklist:**
- [ ] Model selection interface
- [ ] Training pipeline
- [ ] Results visualization
- [ ] Feature importance
- [ ] Predictions
- [ ] Build passes
- [ ] Lint passes

---

## Phase 6 — AI Assistant

**Objective:** Enable natural language interaction with datasets.

**Features:**
- Chat interface for querying data
- Natural language to SQL/Pandas translation
- Automatic chart generation from questions
- AI-generated explanations
- Data recommendations

**Deliverables:**
- Chat UI
- Query engine
- Auto-visualization
- Insight generation

**Technologies:**
- Ollama (local LLM)
- Gemini API (optional)

**Folder Changes:**
- `src/features/assistant/` — components, services
- `backend/services/ai/` — LLM integration

**Completion Checklist:**
- [ ] Chat interface
- [ ] Natural language querying
- [ ] Auto chart generation
- [ ] AI explanations
- [ ] Recommendations
- [ ] Build passes
- [ ] Lint passes

---

## Phase 7 — Reports

**Objective:** Generate exportable business reports.

**Features:**
- PDF export
- Downloadable reports
- Business insights summaries
- Custom report builder

**Deliverables:**
- Report generation pipeline
- PDF renderer
- Download interface

**Technologies:**
- PDF generation library
- Report templating

**Folder Changes:**
- `src/features/reports/` — components, services
- `backend/services/reports/` — PDF generation

**Completion Checklist:**
- [ ] Report builder
- [ ] PDF export
- [ ] Business insights
- [ ] Summaries
- [ ] Build passes
- [ ] Lint passes

---

## Phase 8 — Deployment

**Objective:** Production-ready deployment with CI/CD.

**Features:**
- Docker containerization
- CI/CD pipeline
- Performance optimization
- Production configuration
- Monitoring setup

**Deliverables:**
- Dockerfile and docker-compose
- GitHub Actions workflow
- Production build optimization
- Deployment to Vercel + Render

**Technologies:**
- Docker
- GitHub Actions
- Vercel, Render

**Folder Changes:**
- `Dockerfile`, `docker-compose.yml`
- `.github/workflows/`
- Production config files

**Completion Checklist:**
- [ ] Docker setup
- [ ] CI/CD pipeline
- [ ] Performance optimization
- [ ] Production deployment
- [ ] Monitoring
- [ ] Documentation finalized
