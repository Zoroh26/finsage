# Finsage FastAPI Project

## Installation Guide

### 1. Clone the repository
```sh
git clone <your-repo-url>
cd finsage
```

### 2. Create a virtual environment
```sh
python -m venv venv
```

### 3. Activate the virtual environment
- **Windows (PowerShell):**
  ```sh
  .\venv\Scripts\Activate.ps1
  ```
- **Windows (cmd):**
  ```sh
  venv\Scripts\activate.bat
  ```
- **Linux/macOS:**
  ```sh
  source venv/bin/activate
  ```

### 4. Install dependencies
```sh
pip install -r requirements.txt
```

### 5. Run the FastAPI server
- If your main file is `main.py` in the root:
  ```sh
  uvicorn main:app --reload
  ```
- If your main file is in the `app` folder:
  ```sh
  uvicorn app.main:app --reload
  ```

### 6. Access the API
Open your browser and go to:
- [http://127.0.0.1:8000](http://127.0.0.1:8000) — Main API
- [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) — Interactive Swagger UI

---

## Project Structure
```
main.py
requirements.txt
controllers/
core/
models/
router/
routes/
services/
utills/
```

---

## Troubleshooting
- If `uvicorn` is not recognized, ensure your virtual environment is activated and run `pip install uvicorn fastapi`.
- For additional dependencies, add them to `requirements.txt` and run `pip install -r requirements.txt` again.

---

## License
MIT
