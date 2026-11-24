# 클라우드 네이티브 게시판

클라우드네이티브와운영기술 기말 프로젝트 (이하윤, 60242049)

```
브라우저 → 127.0.0.1:2000 → (VirtualBox) → 10.0.2.20:80 (MetalLB) → ingress-nginx
            ├─ /api → board-backend-service  → Flask 파드 (gunicorn :8001) → PostgreSQL (myserver01 10.0.2.4:5432)
            └─ /    → board-frontend-service → nginx 파드 (index.html)

git push(main) → GitHub Actions: 이미지 빌드 → Docker Hub push → k8s/ 이미지 태그 커밋 → ArgoCD 자동 Sync
```

| 폴더 | 내용 |
|---|---|
| `backend/` | Flask CRUD API (`/api/posts`, `/api/health`), Dockerfile |
| `frontend/` | 게시판 화면 (HTML + JS), nginx Dockerfile |
| `k8s/` | Deployment, Service, Secret, Ingress (ArgoCD 가 감시하는 폴더) |
| `.github/workflows/ci.yml` | main push 시 자동 빌드·배포 워크플로 |
