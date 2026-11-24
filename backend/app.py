# 게시판 백엔드 (Flask + PostgreSQL)
# 이하윤 (60242049) - 클라우드네이티브와운영기술 기말 프로젝트
import os
import socket
import time

import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, request

app = Flask(__name__)
app.json.ensure_ascii = False  # 한글을 그대로 JSON 으로 응답

# DB 접속 정보는 쿠버네티스 Deployment의 env / Secret 으로 주입
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "10.0.2.4"),
    "port": int(os.environ.get("DB_PORT", "5432")),
    "dbname": os.environ.get("DB_NAME", "board"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", ""),
}
APP_VERSION = os.environ.get("APP_VERSION", "dev")


def get_conn():
    return psycopg2.connect(**DB_CONFIG, connect_timeout=5)


def init_db(retries=10):
    """테이블이 없으면 생성. DB가 늦게 뜰 수 있으니 몇 번 재시도."""
    for i in range(retries):
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS posts (
                        id         SERIAL PRIMARY KEY,
                        title      VARCHAR(200) NOT NULL,
                        content    TEXT NOT NULL,
                        author     VARCHAR(50)  NOT NULL DEFAULT '익명',
                        created_at TIMESTAMP    NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMP    NOT NULL DEFAULT NOW()
                    )
                    """
                )
            print("DB 준비 완료", flush=True)
            return
        except psycopg2.Error as e:
            print(f"DB 연결 재시도 {i + 1}/{retries}: {e}", flush=True)
            time.sleep(3)


def row_to_dict(row):
    d = dict(row)
    for key in ("created_at", "updated_at"):
        if d.get(key) is not None:
            d[key] = d[key].strftime("%Y-%m-%d %H:%M:%S")
    return d


def read_body():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()
    author = (data.get("author") or "").strip() or "익명"
    return title, content, author


# ---------- 상태 확인용 ----------
@app.get("/api/health")
def health():
    # pod 이름(hostname)과 버전을 보여주면 로드밸런싱·CI/CD 시연에 좋음
    return jsonify(status="ok", pod=socket.gethostname(), version=APP_VERSION)


# ---------- CRUD ----------
@app.get("/api/posts")
def list_posts():
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM posts ORDER BY id DESC")
        return jsonify([row_to_dict(r) for r in cur.fetchall()])


@app.get("/api/posts/<int:post_id>")
def get_post(post_id):
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
        row = cur.fetchone()
    if row is None:
        return jsonify(error="게시글이 없습니다"), 404
    return jsonify(row_to_dict(row))


@app.post("/api/posts")
def create_post():
    title, content, author = read_body()
    if not title or not content:
        return jsonify(error="제목과 내용을 입력하세요"), 400
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "INSERT INTO posts (title, content, author) VALUES (%s, %s, %s) RETURNING *",
            (title, content, author),
        )
        row = cur.fetchone()
    return jsonify(row_to_dict(row)), 201


@app.put("/api/posts/<int:post_id>")
def update_post(post_id):
    title, content, author = read_body()
    if not title or not content:
        return jsonify(error="제목과 내용을 입력하세요"), 400
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """UPDATE posts SET title = %s, content = %s, author = %s, updated_at = NOW()
               WHERE id = %s RETURNING *""",
            (title, content, author, post_id),
        )
        row = cur.fetchone()
    if row is None:
        return jsonify(error="게시글이 없습니다"), 404
    return jsonify(row_to_dict(row))


@app.delete("/api/posts/<int:post_id>")
def delete_post(post_id):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM posts WHERE id = %s", (post_id,))
        deleted = cur.rowcount
    if deleted == 0:
        return jsonify(error="게시글이 없습니다"), 404
    return jsonify(result="deleted", id=post_id)


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001)
