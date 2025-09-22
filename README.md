# PromptOps

**Optimizes & Tests prompts for LLM with PromptOps**

A comprehensive platform for testing and evaluating large language model (LLM) prompts through systematic perturbation analysis and robustness testing. This project enables researchers and developers to assess prompt reliability across different LLM providers and testing scenarios.

## 🚀 Features

### Core Capabilities
- **Multi-LLM Support**: Integration with OpenAI GPT and Google Gemini
- **Prompt Testing Framework**: Systematic testing with perturbation analysis
- **Interactive Web Interface**: Drag-and-drop project builder with real-time testing
- **Robustness Analysis**: 10+ perturbation types including taxonomy, NER, temporal, negation, and fairness
- **Score Comparison**: Visualization and analysis of model performance across different configurations
- **Applicability Check**: Automated assessment of which perturbations are relevant for your data

### Testing Types
- **Sentiment Analysis**: Test sentiment classification robustness
- **Question Answering**: Evaluate QA performance with and without context
- **Custom Prompts**: Build and test your own prompt configurations

### Supported Models
- OpenAI: GPT-3.5, GPT-4, GPT-4o
- Google Gemini: 2.0 Flash

## 🏗️ Architecture

### Frontend (Next.js)
- **React-based UI** with TypeScript
- **Drag-and-drop interface** for building test configurations
- **Real-time dashboards** with Chart.js visualizations
- **Authentication system** with NextAuth.js
- **Project management** with MongoDB integration

### Backend (FastAPI)
- **RESTful API** with automatic documentation
- **Celery task queue** for async processing
- **Redis** for caching and session management
- **Comprehensive testing suite** with 10+ perturbation types
- **Multi-format export** (JSON, CSV, Excel)

### Infrastructure
- **Docker containerization** with multi-service orchestration
- **Nginx reverse proxy** with SSL support
- **Horizontal scaling** with worker processes
- **Health monitoring** and logging

## 📦 Installation

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for development)
- Python 3.8+ (for local development)

### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone https://github.com/MUICT-SERU/SP2024-Noppomummum.git
   cd SP2024-Noppomummum
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   cp api/.env.example api/.env
   # Edit the files with your configuration
   ```

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Web Interface: http://localhost:3000

### Development Setup

1. **Install dependencies**
   ```bash
   # Frontend
   pnpm install
   
   # Backend
   cd api && pip install -r requirements.txt
   ```

2. **Start development services**
   ```bash
   # Start MongoDB and Redis
   docker-compose up redis -d
   
   # Start backend
   cd api && uvicorn index:app --reload --port 5328
   
   # Start frontend
   pnpm dev
   ```

## 🔧 Configuration

### Environment Variables

**Frontend (.env)**
```env
NEXTAUTH_SECRET=your-nextauth-secret-key-here
NEXTAUTH_URL=http://localhost:3000
MONGODB_URI=mongodb://localhost:27017/promptops
FASTAPI_URL=http://localhost:5328
NEXT_PUBLIC_FASTAPI_URL=http://localhost:5328
NEXT_PUBLIC_API_KEY=your-api-key-here
API_KEY_ENCRYPTION_KEY=your-32-character-encryption-key-here
```

**Backend (api/.env)**
```env
API_KEY=your-api-key-here
REDIS_URL=redis://redis:6379
ALLOWED_ORIGINS=http://localhost:3000
HTTPS_REDIRECT=FALSE
API_KEY_ENCRYPTION_KEY=your-32-character-encryption-key-here
```

### API Keys
Configure your LLM provider API keys in the web interface:
- OpenAI API Key
- Google Gemini API Key

## 📚 Usage

### Creating a Test Project

1. **Navigate to the dashboard** and click "New Project"
2. **Select project type**: Sentiment Analysis, QA with Context, or QA without Context
3. **Configure LLM settings**: Choose your model provider and settings
4. **Upload test data**: CSV file with your prompts and expected results
5. **Select perturbations**: Choose which robustness tests to apply
6. **Run tests**: Execute the test suite and view results

### Understanding Results

- **Similarity Scores**: Cosine similarity between original and perturbed responses
- **Robustness Metrics**: Performance degradation under perturbations
- **Applicability Analysis**: Which perturbations are relevant for your data
- **Comparative Analysis**: Side-by-side model performance comparison

## 🧪 Perturbation Types

1. **Taxonomy**: Semantic word replacement using WordNet hierarchies
2. **Named Entity Recognition (NER)**: Entity substitution while preserving context
3. **Temporal**: Time-related modifications and temporal logic changes
4. **Negation**: Logical negation insertion and removal
5. **Coreference**: Pronoun resolution and reference changes
6. **Semantic Role Labeling (SRL)**: Argument structure modification
7. **Logic**: Logical operator and connector changes
8. **Vocabulary**: Synonym replacement and lexical variations
9. **Fairness**: Bias detection through demographic attribute changes
10. **Robustness**: General stress testing with noise and variations

Each perturbation type includes:
- **Applicability checking**: Automatic detection if perturbation applies to your data
- **Severity levels**: Control the intensity of modifications
- **Context preservation**: Maintain semantic meaning while introducing variations
- **Batch processing**: Apply perturbations to entire datasets efficiently

## 📊 Evaluation Result

### With Context
![GPT-4o With Context](images/with_context_gpt.png)
![Gemini With Context](images/with_context_gemini.png)

### Without Context
![GPT-4o Without Context](images/without_context_gpt.png)
![Gemini Without Context](images/without_context_gemini.png)


## 🙏 Acknowledgments

This project is based on research from "Test It Before You Trust It: Applying Software Testing for Trustworthy In-context Learning" and builds upon various open-source libraries and frameworks:

- **Next.js and React ecosystem** for the frontend interface
- **FastAPI and Python data science stack** for backend processing
- **Redis and Celery** for distributed task processing
- **Chart.js and Recharts** for data visualization
- **Docker** for containerization and deployment
- **NLTK, spaCy, and transformers** for natural language processing
- **OpenAI, Google AI** for LLM integrations
