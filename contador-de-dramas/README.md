
# 🎭 Contador de Dramas

Aplicação web simples para registrar e acompanhar **dramas**, com CRUD de **Usuários** (nome, apelido) e **Dramas** (drama, descrição, intensidade 0-10 com emojis).

## Tecnologias
- Flask (Python) + Jinja2
- SQLAlchemy (SQLite local por padrão; compatível com PostgreSQL via `DATABASE_URL`)
- Bootstrap 5 (tema Cosmo) + Bootstrap Icons

## Rodando localmente
```bash
python -m venv .venv && source .venv/bin/activate  # (ou .venv\Scripts\activate no Windows)
pip install -r requirements.txt
export FLASK_APP=app.py  # Windows: set FLASK_APP=app.py
python app.py
```
Acesse: http://localhost:5000

## Deploy (Render)
1. Suba este código em um repositório Git (GitHub/GitLab/Bitbucket).
2. No Render.com > New > Web Service > conecte o repositório.
3. Linguagem: **Python**. Build: `pip install -r requirements.txt`.
4. Start: `gunicorn app:app --workers=2 --threads=4 --timeout=120 --bind 0.0.0.0:$PORT`.
5. (Opcional) Adicione um banco **PostgreSQL** e configure `DATABASE_URL` como variável de ambiente.
6. Publique — você terá um link público do tipo `https://contador-de-dramas.onrender.com`.

## Estrutura
```
.
├── app.py                # app Flask + rotas + modelos
├── requirements.txt
├── Procfile
├── Dockerfile
├── render.yaml           # config opcional para Render
├── static/
│   ├── styles.css
│   └── script.js
└── templates/
    ├── base.html
    ├── index.html
    ├── users/
    │   ├── list.html
    │   ├── create.html
    │   └── edit.html
    └── dramas/
        ├── list.html
        ├── create.html
        └── edit.html
```

## Observações
- O banco SQLite (`dramas.db`) é criado automaticamente em ambiente local.
- Em produção, prefira Postgres (Neon/Supabase/Render) via `DATABASE_URL`.
- Intensidade mapeada para emojis: 0😌 1🙂 2😊 3😯 4😕 5😬 6😟 7😫 8😤 9😭 10💥.
