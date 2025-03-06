# 🚀 CO<sub>2</sub>DE Red Dashboard  

Please see the below instructions on how to set up and run the Streamlit dashboard using a **virtual environment**.

## 🛠️ Setup Instructions  

### 1️⃣ **Create a Virtual Environment**  
It’s recommended to use a virtual environment to manage dependencies:  

#### **For Windows (cmd/PowerShell):**  
```sh
python -m venv venv
venv\Scripts\activate
```

#### **For macOS/Linux (Terminal):**  
```sh
python3 -m venv venv
source venv/bin/activate
```

---

### 2️⃣ **Install Dependencies**  
Once the virtual environment is activated, install the required dependencies:  
```sh
pip install -r requirements.txt
```

---

### 3️⃣ **Run the Streamlit App**  
To start the dashboard, run:  
```sh
streamlit run dashboard.py
```

---

### 4️⃣ **Stop the App**  
To stop the running Streamlit app, press `CTRL + C` in the terminal.

---

### 5️⃣ **Deactivate the Virtual Environment**  
When you're done, deactivate the virtual environment with:  
```sh
deactivate
```

---

## 🔧 **Troubleshooting**  

- If **Streamlit is not found**, install it manually:  
  ```sh
  pip install streamlit
  ```
- If `requirements.txt` is missing, create one with:  
  ```sh
  pip freeze > requirements.txt
  ```

Now you’re ready to run your **Streamlit dashboard**! 🚀🎉  

