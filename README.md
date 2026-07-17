# Campus Circle Event App

大学生向けのサークル検索・イベント告知モバイルアプリです。

## 構成

- モバイルアプリ: React Native / Expo / TypeScript
- フロントエンド: Next.js / TypeScript
- バックエンド: FastAPI / Python
- データベース: PostgreSQL 16
- 実行環境: Docker Compose（FastAPI・PostgreSQL）

モバイルアプリは `mobile` ディレクトリにあります。現在のNext.js画面は技術検証用のWebフロントエンドです。

データは `PostgreSQL -> FastAPI -> React Native` の順に取得する構成で開発します。

## モバイルアプリ

```bash
cd ~/Developer/campus-circle-event-app/mobile
npm install
npm start
```

詳しい操作は `mobile/README.md` を参照してください。

## Web・API起動方法

1. Docker Desktopを起動します。
2. FastAPIとPostgreSQLを起動します。

```bash
cd ~/Developer/campus-circle-event-app/backend
docker compose up -d --build
```

3. 接続状態を確認します。

```bash
curl http://localhost:8000/health
```

`{"status":"ok","database":"connected"}` と表示されれば、FastAPIとPostgreSQLの接続は成功です。

4. Next.jsを起動します。

```bash
cd ~/Developer/campus-circle-event-app
npm run dev
```

5. ブラウザで http://localhost:3000 を開きます。

## 主な確認先

- Webアプリ: http://localhost:3000
- FastAPIヘルスチェック: http://localhost:8000/health
- FastAPIドキュメント: http://localhost:8000/docs
- サークルAPI: http://localhost:8000/api/circles
- イベントAPI: http://localhost:8000/api/events

## 終了方法

Next.jsを起動したTerminalで `Control + C` を押します。その後、Dockerを停止します。

```bash
cd ~/Developer/campus-circle-event-app/backend
docker compose down
```

PostgreSQLのデータはDocker volumeに保存されるため、通常の `docker compose down` では削除されません。
