# n8n GPU Middleware

## Overview
The n8n GPU Middleware project is designed to integrate GPU capabilities into the n8n workflow automation tool. This middleware allows users to execute GPU tasks seamlessly, leveraging Vast.ai for GPU resource management.

## Project Structure
```
n8n-gpu-middleware
├── src
│   ├── main.py                # Entry point for the FastAPI application
│   ├── middleware
│   │   └── gpu_integration.py  # Middleware for GPU integration
│   ├── api
│   │   └── routes.py          # API route definitions
│   ├── services
│   │   └── gpu_service.py      # Service logic for GPU tasks
│   ├── models
│   │   └── gpu_task.py         # Data models for GPU tasks
│   └── config
│       └── settings.py         # Configuration settings
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── tests
│   ├── test_gpu_integration.py  # Unit tests for GPU integration
│   └── test_api.py             # Unit tests for API routes
└── .gitignore                  # Git ignore file
```

## Setup Instructions
1. Clone the repository:
   ```
   git clone <repository-url>
   cd n8n-gpu-middleware
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure your environment variables or settings in `src/config/settings.py`.

## Usage
To run the FastAPI application, execute the following command:
```
uvicorn src.main:app --reload
```

You can access the API documentation at `http://localhost:8000/docs`.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.