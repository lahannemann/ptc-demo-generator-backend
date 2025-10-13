# AiDemoDataGenerator

## ✅ **Project Setup Guide**

### 1. **Clone and Open in IntelliJ**
- Clone the repository.
- Open the project in IntelliJ.

---

### 2. **Configure Python**
- Ensure **Python 3.12** is installed on your system.
- In IntelliJ:
  - Go to **File → Project Structure → Project → SDK**.
  - Select your installed Python interpreter from the dropdown (no need to add if it’s already detected).

---

### 3. **Create a Python SDK Module (New Virtual Environment)**
- Navigate to **Project Structure → Modules → Module SDK dropdown**.
- Click **Add SDK → Python SDK → OK**.
  - This creates a new **virtual environment (venv)** for the module.

---

### 4. **Activate Virtual Environment**
- Open a terminal (either in IntelliJ or your system terminal).
- Navigate to the project root directory.
- Activate the venv:
  - **Windows**:
    ```bash
    .\venv\Scripts\activate
    ```
  - **macOS/Linux**:
    ```bash
    source venv/bin/activate
    ```

---

### 5. **Prepare Dependencies**
- Copy the `python-client` folder into the project root.
- Create a `.env` file and add your API key.
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```
- If `openapi_client` is not working:
  ```bash
  cd python-client
  pip install .
  ```

---

### 6. **Update IntelliJ Module SDK**
- Go back to **Project Structure → Modules**.
- Select **ptc-demo-generator-backend SDK** from the dropdown.

---

### 7. **Run the Backend**
- From the terminal in the project root:
  ```bash
  uvicorn main:app --host 0.0.0.0 --port 8000
  ```

---

### 8. **Verify**
- Visit:
  ```
  http://localhost:8000/api/greet
  ```
- Expected response:
  ```json
  {"message": "Hello unknown!"}
  ```
