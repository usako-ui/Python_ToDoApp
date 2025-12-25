from flask import Flask, render_template, request, redirect, url_for, flash
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os
import json
from dotenv import load_dotenv

# --------------------
# 環境変数
# --------------------
load_dotenv()

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "replace-me")

# Render / 本番用（JSON文字列）
SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

# ローカル確認用（任意）
SERVICE_ACCOUNT_FILE = os.getenv(
    "SERVICE_ACCOUNT_FILE",
    "service_account.json"
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# --------------------
# Flask
# --------------------
app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY


# --------------------
# Google Sheets（サービスアカウント）
# --------------------
def get_sheet():
    # ① Render / 本番（環境変数）
    if SERVICE_ACCOUNT_JSON:
        info = json.loads(SERVICE_ACCOUNT_JSON)
        creds = Credentials.from_service_account_info(
            info, scopes=SCOPES
        )

    # ② ローカル（JSONファイル）
    else:
        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )

    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID).sheet1


# --------------------
# 次のタスクID生成（3桁通番）
# --------------------
def generate_next_task_id(sheet):
    records = sheet.get_all_records()
    ids = []

    for r in records:
        try:
            ids.append(int(r.get("タスクID", 0)))
        except:
            pass

    next_id = max(ids) + 1 if ids else 1
    return str(next_id).zfill(3)


# --------------------
# シート → タスク
# --------------------
def sheet_to_tasks(sheet):
    records = sheet.get_all_records()
    tasks = []

    for r in records:
        tasks.append({
            "ID": str(r.get("タスクID", "")).strip(),
            "Title": r.get("タイトル", "").strip(),
            "Content": r.get("内容", ""),
            "DueDate": r.get("期日", ""),
            "Completed": str(r.get("完了フラグ", "")).lower() == "true",
            "Source": r.get("登録元", "manual"),
            "EventID": r.get("イベントID", "")
        })

    def parse_due(d):
        if not d:
            return datetime.max
        for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(d, fmt)
            except:
                pass
        return datetime.max

    return sorted(tasks, key=lambda x: parse_due(x["DueDate"]))


# --------------------
# トップ
# --------------------
@app.route("/")
def index():
    sheet = get_sheet()
    tasks = sheet_to_tasks(sheet)

    return render_template(
        "index.html",
        tasks=tasks,
        now=datetime.now().strftime("%Y-%m-%dT%H:%M")
    )


# --------------------
# 一覧（フィルタ対応）
# --------------------
@app.route("/tasks")
def task_list():
    sheet = get_sheet()
    tasks = sheet_to_tasks(sheet)

    filter_mode = request.args.get("filter")
    if filter_mode == "todo":
        tasks = [t for t in tasks if not t["Completed"]]

    return render_template(
        "tasks.html",
        tasks=tasks,
        filter_mode=filter_mode,
        now=datetime.now().strftime("%Y-%m-%dT%H:%M")
    )


# --------------------
# 追加
# --------------------
@app.route("/add", methods=["POST"])
def add():
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    duedate = request.form.get("duedate", "").strip()

    if not title or not duedate:
        flash("タイトルと期日は必須です。")
        return redirect(url_for("index"))

    sheet = get_sheet()
    task_id = generate_next_task_id(sheet)

    sheet.append_row([
        task_id,
        title,
        content,
        duedate,
        "False",
        "manual",
        ""
    ])

    flash(f"タスク {task_id} を追加しました。")
    return redirect(url_for("index"))


# --------------------
# 編集
# --------------------
@app.route("/edit/<task_id>")
def edit(task_id):
    sheet = get_sheet()
    records = sheet.get_all_records()

    for r in records:
        if str(r.get("タスクID", "")).strip() == task_id:
            task = {
                "ID": task_id,
                "Title": r.get("タイトル", ""),
                "Content": r.get("内容", ""),
                "DueDate": r.get("期日", "")
            }
            return render_template("edit.html", task=task)

    flash("タスクが見つかりません。")
    return redirect(url_for("task_list"))


# --------------------
# 更新
# --------------------
@app.route("/update/<task_id>", methods=["POST"])
def update(task_id):
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    duedate = request.form.get("duedate", "").strip()

    if not title or not duedate:
        flash("タイトルと期日は必須です。")
        return redirect(url_for("task_list"))

    sheet = get_sheet()
    records = sheet.get_all_records()

    for idx, r in enumerate(records, start=2):
        if str(r.get("タスクID", "")) == task_id:
            sheet.update(
                f"A{idx}:G{idx}",
                [[
                    task_id,
                    title,
                    content,
                    duedate,
                    r.get("完了フラグ", "False"),
                    r.get("登録元", "manual"),
                    r.get("イベントID", "")
                ]]
            )
            flash("タスクを更新しました。")
            return redirect(url_for("task_list"))

    flash("タスクが見つかりません。")
    return redirect(url_for("task_list"))


# --------------------
# 完了切替
# --------------------
@app.route("/toggle/<task_id>", methods=["POST"])
def toggle(task_id):
    sheet = get_sheet()
    records = sheet.get_all_records()

    for idx, r in enumerate(records, start=2):
        if str(r.get("タスクID", "")).strip() == task_id:
            current = str(r.get("完了フラグ", "")).lower() == "true"
            new_value = "False" if current else "True"
            sheet.update_cell(idx, 5, new_value)
            return redirect(request.referrer or url_for("task_list"))

    flash("タスクが見つかりません。")
    return redirect(url_for("task_list"))


# --------------------
# 削除
# --------------------
@app.route("/delete/<task_id>", methods=["POST"])
def delete(task_id):
    sheet = get_sheet()
    records = sheet.get_all_records()

    for idx, r in enumerate(records, start=2):
        if str(r.get("タスクID", "")) == task_id:
            sheet.delete_rows(idx)
            flash(f"タスク {task_id} を削除しました。")
            return redirect(url_for("task_list"))

    flash("タスクが見つかりません。")
    return redirect(url_for("task_list"))


# --------------------
# 完了タスク一括削除
# --------------------
@app.route("/delete_completed", methods=["POST"])
def delete_completed():
    sheet = get_sheet()
    records = sheet.get_all_records()

    for idx in range(len(records), 0, -1):
        r = records[idx - 1]
        if str(r.get("完了フラグ", "")).lower() == "true":
            sheet.delete_rows(idx + 1)

    flash("完了済みタスクを一括削除しました。")
    return redirect(url_for("task_list"))


# --------------------
# 実行
# --------------------
if __name__ == "__main__":
    app.run(debug=True)
