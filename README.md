# 📋 Flask ToDo App（Googleスプレッドシート連携）

Flask + Googleスプレッドシートをデータベース代わりに使った  
**シンプルな ToDo 管理アプリ**です。

- タスク追加／編集／削除
- 完了チェック（1クリック）
- 期限切れタスクは赤表示
- 完了済みは打ち消し線＋薄色
- 完了タスクの一括削除
- Render（無料プラン）対応

---

## 🚀 デモ構成

- フロントエンド：HTML（Bootstrap）
- バックエンド：Flask
- データ保存：Googleスプレッドシート
- 認証方式：**Google サービスアカウント**
- デプロイ：Render（無料プラン）

---

## 📁 ディレクトリ構成

```text
project-root/
├─ app2.py                  # メインアプリ（サービスアカウント版）
├─ requirements.txt         # Render用依存関係
├─ templates/
│   ├─ index.html
│   ├─ tasks.html
│   └─ edit.html
├─ static/
├─ .env                     # 環境変数（Git管理外）
├─ service_account.json     # サービスアカウント鍵（Git管理外）
├─ .gitignore
└─ README.md

🔐 必要な環境変数（.env）
SPREADSHEET_ID=xxxxxxxxxxxxxxxxxxxx
FLASK_SECRET_KEY=your-secret-key
GOOGLE_APPLICATION_CREDENTIALS=service_account.json

🔎 補足

SPREADSHEET_ID
→ GoogleスプレッドシートのURLに含まれるID

service_account.json
→ Google Cloud で作成したサービスアカウントの鍵ファイル
→ GitHub・Renderに直接アップしない

📄 Googleスプレッドシート構成

1行目はヘッダー行として以下を用意：

タスクID	タイトル	内容	期日	完了フラグ	登録元	イベントID

完了フラグ：True / False

タスクID：3桁連番（001, 002, …）

🛠️ ローカル実行方法
# 仮想環境作成（任意）
python -m venv venv
source venv/bin/activate  # Windowsは venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# 起動
python app2.py


👉 ブラウザで
http://127.0.0.1:5000

⚠️ セキュリティ注意

.env

service_account.json

OAuth版ファイル

これらは 必ず .gitignore に含めること。