# VERAMOD - Technology Stack

## Programming Languages
- **TypeScript 5.3+**: Frontend development with type safety
- **Python 3.8+**: Backend API and service logic
- **CSS3**: Styling without external UI frameworks

## Frontend Technologies

### Core Framework
- **React 18.2**: Component-based UI library
- **React DOM 18.2**: DOM rendering
- **Vite 5.0**: Fast build tool and dev server

### Routing & State
- **React Router DOM 6.20**: Client-side routing
- **React Context**: State management for authentication

### UI & UX
- **React Hot Toast 2.6**: Notification system
- **Custom CSS**: Enterprise styling without external libraries
- **Particle Background**: Custom animated background component

### Authentication
- **AWS Amplify 6.0**: Authentication and AWS integration

## Backend Technologies

### Web Framework
- **FastAPI**: High-performance async API framework
- **Uvicorn**: ASGI server for FastAPI applications

### Data & Validation
- **Pydantic**: Data validation and serialization
- **SQLite**: Lightweight database for analysis metadata
- **Python Typing**: Type hints for code clarity

### AWS Integration
- **Boto3**: AWS SDK for Python
- **AWS S3**: Object storage for analysis artifacts
- **AWS SNS**: Email notifications
- **AWS Bedrock**: AI/ML services for chat functionality

### External Tools
- **Transform (atx)**: Code analysis and documentation generation
- **GitHub API**: Repository access and cloning

## Development Tools

### Build & Development
```bash
# Frontend development
npm run dev          # Start Vite dev server
npm run build        # Build for production
npm run preview      # Preview production build

# Backend development
uvicorn main:app --reload  # Start FastAPI with hot reload
```

### Configuration Management
- **Environment Variables**: `.env` files for configuration
- **dotenv**: Python environment variable loading
- **Vite Config**: Frontend build configuration

### Code Quality
- **TypeScript**: Static type checking
- **Python Type Hints**: Runtime type validation
- **ESLint/TSConfig**: Code linting and formatting

## Dependencies

### Frontend Dependencies
```json
{
  "aws-amplify": "^6.0.0",
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "react-hot-toast": "^2.6.0",
  "react-router-dom": "^6.20.0"
}
```

### Backend Dependencies
- **fastapi**: Web framework
- **uvicorn**: ASGI server
- **pydantic**: Data validation
- **boto3**: AWS SDK
- **python-dotenv**: Environment management

## Development Environment
- **Node.js**: Required for frontend development
- **Python 3.8+**: Required for backend services
- **AWS CLI**: For cloud service configuration
- **Git**: Version control and repository cloning