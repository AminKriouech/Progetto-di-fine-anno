# 📄 CV Generator

Un’applicazione web per creare, personalizzare e scaricare curriculum vitae in PDF, con sistema di autenticazione e salvataggio dei CV nel cloud.

-----

## 🧩 Descrizione

CV Generator è una web app sviluppata con **Flask** che permette di:

- Compilare un CV tramite un form interattivo
- Scegliere tra 4 template grafici: **Classic**, **Modern**, **Minimal**, **Creative**
- Visualizzare un’anteprima in tempo reale
- Scaricare il CV in formato **PDF**
- **Registrarsi / accedere** con email e password
- **Salvare più CV** sul proprio account e ricaricarli in qualsiasi momento

-----

## 🚀 Come eseguirlo su VS Code

### 1. Clona il repository

```bash
git clone https://github.com/TUO-USERNAME/cv_generator.git
cd cv_generator
```

### 2. Crea e attiva un ambiente virtuale

```bash
python -m venv venv
```

- **Windows:**
  
  ```bash
  venv\Scripts\activate
  ```
- **Mac / Linux:**
  
  ```bash
  source venv/bin/activate
  ```

### 3. Installa le dipendenze

```bash
pip install -r requirements.txt
```

### 4. Avvia l’applicazione

```bash
python app.py
```

### 5. Apri nel browser

Vai su → <http://localhost:5000>

> 💡 **Consiglio:** Installa l’estensione **Python** di Microsoft su VS Code per avere il supporto completo (syntax highlighting, debug, terminale integrato).

-----

## ☁️ Deploy



L’applicazione è pronta per essere deployata su piattaforme come **Render**, **Railway** o **Heroku**.

Prima del deploy ricordarsi di:

- Impostare la variabile d’ambiente `SECRET_KEY` con un valore sicuro
- Sostituire SQLite con un database persistente (es. PostgreSQL)
- Impostare `debug=False` in `app.py`

**URL del deploy:** *da aggiornare dopo il deploy*

-----

## 🛠️ Stack tecnologico

|Tecnologia      |Utilizzo              |
|----------------|----------------------|
|Python / Flask  |Backend e routing     |
|Flask-SQLAlchemy|Database (SQLite)     |
|Flask-Login     |Autenticazione utenti |
|ReportLab       |Generazione PDF       |
|HTML / CSS / JS |Frontend e template CV|

-----

## 📁 Struttura del progetto

```
cv_generator/
├── app.py               # Backend Flask, routes, modelli DB
├── pdf_generator.py     # Logica di generazione PDF
├── requirements.txt     # Dipendenze Python
├── templates/
│   ├── index.html       # Pagina principale (form + anteprima)
│   ├── cv_classic.html  # Template Classic
│   ├── cv_modern.html   # Template Modern
│   ├── cv_minimal.html  # Template Minimal
│   └── cv_creative.html # Template Creative
└── static/              # File statici (CSS, JS, immagini)
```
