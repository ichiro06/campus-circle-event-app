# Upstream

このディレクトリは Cloudflare 公式の security-audit skill を無改変で取り込んだもの（`UPSTREAM.md` を除く）。

Codexのrepository skill path `.agents/skills/security-audit/` は、このcanonical copyへの相対symlinkである。skillの更新とreviewはこのdirectoryだけに行い、Codex aliasは自動的に同じ内容を参照する。

- 取得元: https://github.com/cloudflare/security-audit-skill （`skills/security-audit/`）
- 取り込んだ commit: `c1c8a8c1471069fb0e188eeaff69b8e8db6564a8`（2026-09-14）
- License: MIT（同梱の `LICENSE`、Copyright (c) 2025-2026 Cloudflare, Inc.）
- 取り込み時の確認: 同梱スクリプト（`validate-*.cjs`）は Node 標準の `fs` / `path` / `util` のみを使い、外部送信・依存追加はない。`node --test *.test.cjs` は 65 件 pass。

## 更新手順

1. upstream の `skills/security-audit/` を取得し、このディレクトリへ上書きする（`UPSTREAM.md` は残す）。
2. 差分を review し、外部送信や依存追加が入っていないことを確認する。
3. `node --test .claude/skills/security-audit/*.test.cjs` を実行する。
4. 上記 commit hash を更新して PR にする。
