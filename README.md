# Flask Backend API

This is a [Flask](https://flask.palletsprojects.com/) project using MongoDB for data storage and Pine for vector indeing and embedding.

## Getting Started

First, set up your virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

Then, start the development server:

```bash
python main.py
```

The API will be available at [http://localhost:5000](http://localhost:5000).

## Project Structure

- `app/` - Main application directory
  - `__init__.py` - Flask app initialization
  - `mongo.py` - MongoDB connection and models
  - `parser.py` - Data parsing utilities
  - `pine.py` - Background task scheduling
  - `routes.py` - API endpoints
- `requirements.txt` - Project dependencies
- `main.py` - Application entry point

## Environment Setup

Create a `.env` file in the root directory with the following variables:

```env
FLASK_APP=main.py
FLASK_ENV=development
MONGO_URI=your_mongodb_connection_string
```