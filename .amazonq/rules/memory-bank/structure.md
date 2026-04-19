# VERAMOD - Project Structure

## Directory Organization

### Frontend (`src/`)
```
src/
├── components/          # Reusable UI components
│   ├── Navbar.tsx      # Navigation component
│   └── ParticleBackground.tsx  # Animated background
├── pages/              # Main application pages
│   ├── RepoSelection.tsx      # Repository input page
│   ├── AnalysisResults.tsx    # Analysis viewer page
│   └── AnalysisHistory.tsx    # Historical analysis page
├── contexts/           # React context providers
│   └── AuthContext.tsx # Authentication state management
├── utils/              # Utility functions
│   └── fileTree.ts     # File tree manipulation
├── App.tsx             # Main application component
└── main.tsx            # Application entry point
```

### Backend (`backend/`)
```
backend/
├── services/           # Business logic services
│   ├── bedrock_agent.py   # AWS Bedrock integration
│   ├── db.py             # Database operations
│   ├── s3.py             # AWS S3 operations
│   └── transform.py      # Transform tool integration
├── api.py              # FastAPI route definitions
├── main.py             # FastAPI application entry
├── models.py           # Pydantic data models
├── config.py           # Configuration management
├── github.py           # GitHub API integration
└── chat_validation.py  # Chat response validation
```

### Analysis Outputs (`analysis_outputs/`)
- Stores generated analysis artifacts
- Organized by analysis ID
- Contains documentation, architecture diagrams, and summaries

## Core Components

### Frontend Architecture
- **React 18** with TypeScript for type safety
- **React Router** for client-side routing
- **Vite** for fast development and building
- **AWS Amplify** for authentication integration

### Backend Architecture
- **FastAPI** for high-performance API endpoints
- **SQLite** for analysis metadata storage
- **Pydantic** for data validation and serialization
- **AWS SDK** for cloud service integration

### Key Relationships
- Frontend communicates with backend via REST API
- Backend orchestrates analysis workflows
- Transform tool generates documentation artifacts
- AWS services provide storage and notifications
- Database tracks analysis history and metadata

## Architectural Patterns

### Three-Tier Architecture
1. **Presentation Layer**: React frontend with component-based UI
2. **Business Logic Layer**: FastAPI backend with service modules
3. **Data Layer**: SQLite database and S3 storage

### Service-Oriented Design
- Modular service classes for external integrations
- Separation of concerns between API routes and business logic
- Configuration-driven service initialization

### Event-Driven Notifications
- Asynchronous analysis processing
- SNS-based completion notifications
- Status tracking throughout analysis lifecycle