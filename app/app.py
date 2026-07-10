import os
import time
from datetime import datetime, timezone

import psycopg2
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "db"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "vzeta_db"),
    "user": os.getenv("DB_USER", "vzeta_user"),
    "password": os.getenv("DB_PASSWORD", "vzeta_password"),
}

HTML_TEMPLATE = """
<!doctype html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>VZeta - Contador de visitas</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f2f4f7;
            margin: 0;
            display: grid;
            place-items: center;
            min-height: 100vh;
        }
        .card {
            width: min(90%, 620px);
            background: white;
            border-radius: 14px;
            padding: 32px;
            box-shadow: 0 10px 30px rgba(0,0,0,.10);
            text-align: center;
        }
        .count {
            font-size: 64px;
            font-weight: bold;
            margin: 20px 0;
        }
        .ok {
            color: #16794b;
            font-weight: bold;
        }
        .meta {
            color: #5c6670;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <main class="card">
        <h1>VZeta Web Application</h1>
        <p class="ok">Aplicación y base de datos operativas</p>
        <p>Visitas acumuladas:</p>
        <div class="count">{{ total }}</div>
        <p class="meta">Última visita registrada: {{ timestamp }}</p>
        <p class="meta">Arquitectura: NGINX → Flask → PostgreSQL</p>
    </main>
</body>
</html>
"""


def get_connection(retries: int = 20, delay: int = 3):
    """Conecta a PostgreSQL con reintentos para tolerar el arranque del contenedor."""
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            return psycopg2.connect(**DB_CONFIG)
        except psycopg2.OperationalError as error:
            last_error = error
            app.logger.warning(
                "PostgreSQL aún no está disponible. Intento %s/%s.",
                attempt,
                retries,
            )
            time.sleep(delay)

    raise RuntimeError("No fue posible conectar a PostgreSQL") from last_error


def initialize_database() -> None:
    """Crea la tabla de visitas si todavía no existe."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS visits (
                    id BIGSERIAL PRIMARY KEY,
                    visited_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
        connection.commit()


@app.route("/")
def index():
    """Registra una visita y devuelve el contador acumulado."""
    timestamp = datetime.now(timezone.utc)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO visits (visited_at) VALUES (%s);",
                (timestamp,),
            )
            cursor.execute("SELECT COUNT(*) FROM visits;")
            total = cursor.fetchone()[0]
        connection.commit()

    return render_template_string(
        HTML_TEMPLATE,
        total=total,
        timestamp=timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
    )


@app.route("/health")
def health():
    """Endpoint utilizado por Docker para comprobar la salud de la aplicación."""
    try:
        with get_connection(retries=1, delay=0) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                cursor.fetchone()
        return jsonify(status="ok"), 200
    except Exception as error:
        app.logger.error("Healthcheck fallido: %s", error)
        return jsonify(status="error"), 503


if __name__ == "__main__":
    initialize_database()
    app.run(host="0.0.0.0", port=5000)
