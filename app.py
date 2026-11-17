import html
import json
import os
import tempfile
import threading
import uuid
from pathlib import Path

import streamlit as st

DATA_FILE = Path(__file__).parent / "items.json"

st.set_page_config(page_title="쇼핑 리스트", page_icon="🛒", layout="centered")


# ---------- 저장소 ----------
def load_items():
    """items.json에서 목록을 읽는다. 파일이 없거나 깨졌으면 빈 리스트."""
    try:
        # utf-8-sig: 메모장 등이 붙이는 BOM이 있어도 읽을 수 있게 함
        data = json.loads(DATA_FILE.read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, list):
        return []
    items, seen = [], set()
    for i in data:
        if not isinstance(i, dict) or i.get("id") is None or not i.get("name"):
            continue
        iid = str(i["id"])
        if iid in seen:  # 중복 id는 위젯 key 충돌로 앱이 멈추므로 제외
            continue
        seen.add(iid)
        items.append(
            {"id": iid, "name": str(i["name"]), "checked": bool(i.get("checked", False))}
        )
    return items


def save_items(items):
    """임시 파일에 쓴 뒤 교체(원자적 저장). 성공 여부를 반환."""
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(dir=DATA_FILE.parent, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, DATA_FILE)
        return True
    except OSError:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        return False


@st.cache_resource
def _file_lock():
    """모든 세션이 공유하는 잠금 (스크립트는 매번 재실행되므로 캐시에 보관)."""
    return threading.Lock()


def mutate(fn):
    """파일의 최신 목록을 읽어 변경한 뒤 저장한다.

    세션이 가진 오래된 목록으로 파일을 덮어쓰지 않도록, 항상
    '읽기 → 변경 → 저장'을 잠금 안에서 한 번에 수행한다.
    """
    with _file_lock():
        items = load_items()
        fn(items)
        ok = save_items(items)
    st.session_state["save_error"] = not ok


# ---------- 로직 ----------
def add_item(name):
    mutate(lambda items: items.append(
        {"id": str(uuid.uuid4()), "name": name, "checked": False}
    ))


def update_item(item_id, name):
    def fn(items):
        for item in items:
            if item["id"] == item_id:
                item["name"] = name
    mutate(fn)


def set_checked(item_id, checked):
    def fn(items):
        for item in items:
            if item["id"] == item_id:
                item["checked"] = checked
    mutate(fn)


def delete_item(item_id):
    mutate(lambda items: items.__setitem__(
        slice(None), [i for i in items if i["id"] != item_id]
    ))


def delete_checked():
    mutate(lambda items: items.__setitem__(
        slice(None), [i for i in items if not i["checked"]]
    ))


# ---------- 위젯 콜백 ----------
def on_check(item_id):
    set_checked(item_id, st.session_state[f"chk_{item_id}"])


def start_edit(item_id, current_name):
    st.session_state["editing_id"] = item_id
    st.session_state[f"edit_{item_id}"] = current_name
    st.session_state["edit_error"] = False


def cancel_edit():
    st.session_state["editing_id"] = None
    st.session_state["edit_error"] = False


def save_edit(item_id):
    name = st.session_state.get(f"edit_{item_id}", "").strip()
    if not name:
        st.session_state["edit_error"] = True
        return
    update_item(item_id, name)
    st.session_state["editing_id"] = None
    st.session_state["edit_error"] = False


# ---------- 상태 초기화 ----------
st.session_state.setdefault("editing_id", None)
st.session_state.setdefault("edit_error", False)
st.session_state.setdefault("save_error", False)

# ---------- 스타일 (정적 CSS만 주입, 사용자 입력은 넣지 않음) ----------
CSS = """
<style>
.block-container { padding-top: 2rem; max-width: 640px; }

/* 모바일에서도 한 줄 유지: 컬럼이 세로로 쌓이지 않게 */
div[data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; align-items: center; gap: 0.4rem; }
div[data-testid="stColumn"] { min-width: 0 !important; }

/* 버튼 글자가 줄바꿈되지 않게 */
button p { white-space: nowrap; }
div[data-testid="stForm"] div[data-testid="stColumn"]:last-child { flex: 0 0 auto !important; width: auto !important; }

/* 아이템 이름: 입력한 그대로 보여주고(공백 유지), 긴 이름은 줄바꿈 */
.item-name { white-space: pre-wrap; overflow-wrap: anywhere; line-height: 1.4; }
/* 완료 항목은 취소선 + 흐리게 */
.item-name.done { text-decoration: line-through; opacity: 0.5; }

/* 수정/삭제 버튼은 작고 덜 눈에 띄게 */
[class*="st-key-edit_btn_"] button, [class*="st-key-del_"] button {
    padding: 0.15rem 0.4rem; min-height: 2rem; opacity: 0.6;
}
[class*="st-key-edit_btn_"] button:hover, [class*="st-key-del_"] button:hover { opacity: 1; }
/* 삭제는 위험 동작: 호버 시 빨간색 */
[class*="st-key-del_"] button:hover { color: #e5484d; border-color: #e5484d; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ---------- 화면 ----------
st.title("🛒 쇼핑 리스트")

if st.session_state["save_error"]:
    st.error("저장에 실패했어요. 변경 내용이 유지되지 않을 수 있습니다.")

# 매 실행마다 파일의 최신 목록을 사용 (다른 탭·세션의 변경 반영)
items = load_items()
if st.session_state["editing_id"] not in {i["id"] for i in items}:
    st.session_state["editing_id"] = None

total = len(items)
done = sum(1 for i in items if i["checked"])
st.caption(f"{done} / {total} 완료")
st.progress(done / total if total else 0.0)

with st.form("add_form", clear_on_submit=True, border=False):
    c_in, c_add = st.columns([5, 1])
    new_name = c_in.text_input(
        "아이템", placeholder="살 물건을 입력하세요", label_visibility="collapsed"
    )
    submitted = c_add.form_submit_button("추가", type="primary", use_container_width=True)

if submitted:
    name = new_name.strip()
    if name:
        add_item(name)
        st.rerun()  # 위에서 이미 그려진 진행 현황·목록에 새 항목 반영
    else:
        st.warning("아이템 이름을 입력해주세요.")

if not items:
    st.markdown(
        "<div style='text-align:center; padding:2.5rem 0; opacity:0.7;'>"
        "<div style='font-size:3rem;'>🧺</div>"
        "<div>아직 아이템이 없어요.<br>위에서 추가해보세요!</div></div>",
        unsafe_allow_html=True,
    )

for item in items:
    iid = item["id"]
    with st.container(border=True, key=f"row_{iid}"):
        if st.session_state["editing_id"] == iid:
            c_input, c_save, c_cancel = st.columns([6, 1, 1])
            c_input.text_input(
                "이름 수정", key=f"edit_{iid}", label_visibility="collapsed"
            )
            c_save.button(
                "✔", key=f"save_{iid}", on_click=save_edit, args=(iid,),
                type="primary", help="저장",
            )
            c_cancel.button(
                "✖", key=f"cancel_{iid}", on_click=cancel_edit, help="취소"
            )
            if st.session_state["edit_error"]:
                st.warning("이름을 비워둘 수 없어요.")
        else:
            c_chk, c_name, c_edit, c_del = st.columns([1, 6, 1, 1])
            # 파일 기준 상태를 위젯에 반영 (다른 세션에서 바뀐 값이 남아있지 않게)
            st.session_state[f"chk_{iid}"] = item["checked"]
            c_chk.checkbox(
                "완료 표시",  # 숨김 라벨. 사용자 입력(마크다운 해석됨)을 넣지 않는다
                key=f"chk_{iid}",
                on_change=on_check,
                args=(iid,),
                label_visibility="collapsed",
            )
            # 이름은 HTML 이스케이프한 일반 텍스트로 표시 (마크다운/이모지 변환 없음)
            cls = "item-name done" if item["checked"] else "item-name"
            c_name.html(f'<div class="{cls}">{html.escape(item["name"])}</div>')
            c_edit.button(
                "✏️", key=f"edit_btn_{iid}", on_click=start_edit,
                args=(iid, item["name"]), type="tertiary", help="수정",
            )
            c_del.button(
                "🗑️", key=f"del_{iid}", on_click=delete_item,
                args=(iid,), type="tertiary", help="삭제",
            )

if items:
    st.button(
        "체크된 항목 모두 삭제",
        on_click=delete_checked,
        disabled=not any(i["checked"] for i in items),
        use_container_width=True,
    )
