Este comando diz ao Replit para iniciar o servidor web usando o ficheiro bot.py
run = "gunicorn bot:app"

[env]
PYTHONUNBUFFERED = "1"