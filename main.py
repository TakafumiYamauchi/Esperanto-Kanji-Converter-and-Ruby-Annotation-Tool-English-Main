##  main.py(1つ目)
# main.py (メインの Streamlit アプリ/機能拡充版202502)

import streamlit as st
import re
import io
import json
import pandas as pd  # 必要なら使う
from typing import List, Dict, Tuple, Optional
import streamlit.components.v1 as components
import multiprocessing

#=================================================================
# Streamlit で multiprocessing を使う際、PicklingError 回避のため
# 明示的に 'spawn' モードを設定する必要がある。
#=================================================================
try:
    multiprocessing.set_start_method("spawn")
except RuntimeError:
    pass  # すでに start method が設定済みの場合はここで無視する

#=================================================================
# エスペラント文の(漢字)置換・ルビ振りなどを行う独自モジュールから
# 関数をインポートする。
# esp_text_replacement_module.py内に定義されているツールをまとめて呼び出す
#=================================================================
from esp_text_replacement_module import (
    x_to_circumflex,
    x_to_hat,
    hat_to_circumflex,
    circumflex_to_hat,
    replace_esperanto_chars,
    import_placeholders,
    orchestrate_comprehensive_esperanto_text_replacement,
    parallel_process,
    apply_ruby_html_header_and_footer
)

#=================================================================
# Streamlit の @st.cache_data デコレータを使い、読み込み結果をキャッシュして
# JSONファイルのロード高速化を図る。大きなJSON(50MB程度)を都度読むと遅いので、
# ここで呼び出す関数をキャッシュする作り。
#=================================================================
@st.cache_data
def load_replacements_lists(json_path: str) -> Tuple[List, List, List]:
    """
    JSONファイルをロードし、以下の3つのリストをタプルとして返す:
    1) replacements_final_list
    2) replacements_list_for_localized_string
    3) replacements_list_for_2char
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    replacements_final_list = data.get(
        "全域替换用のリスト(列表)型配列(replacements_final_list)", []
    )
    replacements_list_for_localized_string = data.get(
        "局部文字替换用のリスト(列表)型配列(replacements_list_for_localized_string)", []
    )
    replacements_list_for_2char = data.get(
        "二文字词根替换用のリスト(列表)型配列(replacements_list_for_2char)", []
    )
    return (
        replacements_final_list,
        replacements_list_for_localized_string,
        replacements_list_for_2char,
    )

#=================================================================
# Streamlit ページの見た目設定
# page_title: ブラウザタブに表示されるタイトル
# layout="wide" で横幅を広く使えるUIにする
#=================================================================
st.set_page_config(page_title="Esperanto Text (Kanji) Replacement Tool", layout="wide")

# タイトル部分（ユーザーに見える部分を英語化）
st.title("Extended Tool for Replacing Esperanto Text with Kanji and Adding Ruby Annotations")

st.write("---")

#=================================================================
# 1) JSONファイル (置換ルール) をロード
#   (デフォルトを使うか、ユーザーがアップロードするかの選択)
#=================================================================
# ラジオボタンの表示ラベルと実際の値を分ける
radio_json_options_display = {
    "Use the default JSON file": "デフォルトを使用する",
    "Upload a JSON file": "アップロードする"
}

selected_option_display = st.radio(
    "How would you like to load the replacement JSON file?",
    list(radio_json_options_display.keys())
)
# 実際のコード内部で使う値は日本語のまま
selected_option = radio_json_options_display[selected_option_display]

# Streamlit の折りたたみ (expander) でサンプルJSONのダウンロードを案内
with st.expander("Sample JSON (Replacement JSON file)"):
    # サンプルファイルのパス
    json_file_path = './Appの运行に使用する各类文件/最终的な替换用リスト(列表)(合并3个JSON文件).json'
    # JSONファイルを読み込んでダウンロードボタンを生成
    with open(json_file_path, "rb") as file_json:
        btn_json = st.download_button(
            label="Download the sample replacement JSON file",
            data=file_json,
            file_name="replacement_json_sample.json",
            mime="application/json"
        )

#=================================================================
# 置換ルールとして使うリスト3種を初期化しておく。
# (JSONファイル読み込み後に代入される)
#=================================================================
replacements_final_list: List[Tuple[str, str, str]] = []
replacements_list_for_localized_string: List[Tuple[str, str, str]] = []
replacements_list_for_2char: List[Tuple[str, str, str]] = []

# JSONファイルの読み込み方を分岐
if selected_option == "デフォルトを使用する":
    default_json_path = "./Appの运行に使用する各类文件/最终的な替换用リスト(列表)(合并3个JSON文件).json"
    try:
        # デフォルトJSONをロード
        (replacements_final_list,
         replacements_list_for_localized_string,
         replacements_list_for_2char) = load_replacements_lists(default_json_path)
        st.success("Successfully loaded the default JSON file.")
    except Exception as e:
        st.error(f"Failed to load the JSON file: {e}")
        st.stop()
else:
    # ユーザーがファイルアップロードする場合
    uploaded_file = st.file_uploader("Upload your replacement JSON file (合并3个JSON文件).json format)", type="json")
    if uploaded_file is not None:
        try:
            combined_data = json.load(uploaded_file)
            replacements_final_list = combined_data.get(
                "全域替换用のリスト(列表)型配列(replacements_final_list)", [])
            replacements_list_for_localized_string = combined_data.get(
                "局部文字替换用のリスト(列表)型配列(replacements_list_for_localized_string)", [])
            replacements_list_for_2char = combined_data.get(
                "二文字词根替换用のリスト(列表)型配列(replacements_list_for_2char)", [])
            st.success("Successfully loaded the uploaded JSON file.")
        except Exception as e:
            st.error(f"Failed to load the uploaded JSON file: {e}")
            st.stop()
    else:
        st.warning("No JSON file was uploaded. Stopping the process.")
        st.stop()

#=================================================================
# 2) placeholders (占位符) の読み込み
#    %...% や @...@ で囲った文字列を守るために使用する文字列群を読み込む
#=================================================================
placeholders_for_skipping_replacements: List[str] = import_placeholders(
    './Appの运行に使用する各类文件/占位符(placeholders)_%1854%-%4934%_文字列替换skip用.txt'
)
placeholders_for_localized_replacement: List[str] = import_placeholders(
    './Appの运行に使用する各类文件/占位符(placeholders)_@5134@-@9728@_局部文字列替换结果捕捉用.txt'
)

st.write("---")

#=================================================================
# 設定パラメータ (UI) - 高度な設定
# 並列処理 (multiprocessing) を利用できるかどうかのスイッチと、
# 同時プロセス数の選択
#=================================================================
st.header("Advanced Settings (Parallel Processing)")
with st.expander("Open settings for parallel processing"):
    st.write("""
    Here, you can configure how many processes are used for parallel processing 
    when performing text (Kanji) replacements.
    """)
    use_parallel = st.checkbox("Enable parallel processing", value=False)
    num_processes = st.number_input("Number of parallel processes", min_value=2, max_value=4, value=4, step=1)

st.write("---")

#=================================================================
# 例: 出力形式の選択
# (HTMLルビ形式・括弧形式・文字列のみ など)
#=================================================================

# 「format_type」自体の実際の値は元のまま、表示だけ英語化
options = {
    # ユーザーに見せるラベル: 実際の内部値
    'HTML Ruby with size adjustment': 'HTML格式_Ruby文字_大小调整',
    'HTML Ruby with size adjustment + Kanji replacement': 'HTML格式_Ruby文字_大小调整_汉字替换',
    'HTML format only': 'HTML格式',
    'HTML format + Kanji replacement': 'HTML格式_汉字替换',
    'Parentheses format': '括弧(号)格式',
    'Parentheses format + Kanji replacement': '括弧(号)格式_汉字替换',
    'Replace with Kanji (no markup), text only': '替换后文字列のみ(仅)保留(简单替换)'
}

display_options = list(options.keys())
selected_display = st.selectbox(
    "Choose the output format (Please match the format used when creating the replacement JSON):",
    display_options
)
format_type = options[selected_display]

# フォーム外で、変数 processed_text を初期化
processed_text = ""

#=================================================================
# 4) 入力テキストのソースを選択 (手動入力 or ファイルアップロード)
#=================================================================
st.subheader("Source of Input Text")
radio_text_input_display = {
    "Enter text manually": "手動入力",
    "Upload a text file": "ファイルアップロード"
}
source_option_display = st.radio(
    "How would you like to provide the input text?",
    list(radio_text_input_display.keys())
)
source_option = radio_text_input_display[source_option_display]

uploaded_text = ""

# ファイルアップロードが選択された場合
if source_option == "ファイルアップロード":
    text_file = st.file_uploader("Upload a text file (UTF-8)", type=["txt", "csv", "md"])
    if text_file is not None:
        uploaded_text = text_file.read().decode("utf-8", errors="replace")
        st.info("File has been loaded successfully.")
    else:
        st.warning("No file was uploaded. Please switch to manual input or upload a file.")

#=================================================================
# フォーム: 実行ボタン(送信/キャンセル)を配置
#  - テキストエリアにエスペラント文を入力してもらう
#=================================================================
with st.form(key='profile_form'):

    # アップロードテキストがあればそれを初期値にする。
    if uploaded_text:
        initial_text = uploaded_text
    else:
        # セッションステートから 'text0_value' を取得し、それがなければ空文字
        initial_text = st.session_state.get("text0_value", "")

    text0 = st.text_area(
        "Please enter your Esperanto text here:",
        height=150,
        value=initial_text
    )

    # %...% と @...@ の使い方の説明（英語訳）
    st.markdown("""If you enclose a string with “%” (e.g., `%<string up to 50 characters>%`),
    the enclosed part will be **skipped** during Kanji replacements, remaining as is.""")

    st.markdown("""If you enclose a string with “@” (e.g., `@<string up to 18 characters>@`),
    only that locally enclosed part will be replaced with Kanji.""")

    # 出力文字形式 (エスペラント特有文字の表記形式)
    # 実際の値は日本語のままなので、表示用だけ英語にしておく
    letter_type_display = {
        "Use superscript notation": "上付き文字",
        "Use x notation": "x 形式",
        "Use ^ notation": "^形式"
    }
    selected_letter_type_display = st.radio(
        "Choose the output style for special Esperanto characters:",
        list(letter_type_display.keys())
    )
    letter_type = letter_type_display[selected_letter_type_display]

    submit_btn = st.form_submit_button('Submit')
    cancel_btn = st.form_submit_button("Cancel")

    if cancel_btn:
        st.warning("Operation canceled.")
        st.stop()

    if submit_btn:
        st.session_state["text0_value"] = text0

        #=================================================================
        # テキストを置換して処理 (並列 or 単一プロセス)
        #=================================================================
        if use_parallel:
            processed_text = parallel_process(
                text=text0,
                num_processes=num_processes,
                placeholders_for_skipping_replacements=placeholders_for_skipping_replacements,
                replacements_list_for_localized_string=replacements_list_for_localized_string,
                placeholders_for_localized_replacement=placeholders_for_localized_replacement,
                replacements_final_list=replacements_final_list,
                replacements_list_for_2char=replacements_list_for_2char,
                format_type=format_type
            )
        else:
            processed_text = orchestrate_comprehensive_esperanto_text_replacement(
                text=text0,
                placeholders_for_skipping_replacements=placeholders_for_skipping_replacements,
                replacements_list_for_localized_string=replacements_list_for_localized_string,
                placeholders_for_localized_replacement=placeholders_for_localized_replacement,
                replacements_final_list=replacements_final_list,
                replacements_list_for_2char=replacements_list_for_2char,
                format_type=format_type
            )

        #=================================================================
        # letter_typeの指定に応じて、最終的なエスペラント文字の表記を変換
        #=================================================================
        if letter_type == '上付き文字':
            processed_text = replace_esperanto_chars(processed_text, x_to_circumflex)
            processed_text = replace_esperanto_chars(processed_text, hat_to_circumflex)
        elif letter_type == '^形式':
            processed_text = replace_esperanto_chars(processed_text, x_to_hat)
            processed_text = replace_esperanto_chars(processed_text, circumflex_to_hat)

        # HTML形式の場合、ヘッダーとフッターをつける (ルビ表示対応)
        processed_text = apply_ruby_html_header_and_footer(processed_text, format_type)

#=================================================================
# フォーム外の処理: 結果表示・ダウンロード
#=================================================================
if processed_text:
    MAX_PREVIEW_LINES = 250
    lines = processed_text.splitlines()

    if len(lines) > MAX_PREVIEW_LINES:
        first_part = lines[:247]
        last_part = lines[-3:]
        preview_text = "\n".join(first_part) + "\n...\n" + "\n".join(last_part)
        st.warning(
            f"The text is quite long ({len(lines)} lines). "
            "Preview is partially truncated. Showing the first 247 lines and the last 3 lines."
        )
    else:
        preview_text = processed_text

    #=================================================================
    # 置換結果の表示
    #=================================================================
    if "HTML" in format_type:
        tab1, tab2 = st.tabs(["HTML Preview", "Replacement Result (HTML source)"])
        with tab1:
            components.html(preview_text, height=500, scrolling=True)
        with tab2:
            st.text_area("", preview_text, height=300)
    else:
        tab3_list = st.tabs(["Replacement Result"])
        with tab3_list[0]:
            st.text_area("", preview_text, height=300)

    download_data = processed_text.encode('utf-8')
    st.download_button(
        label="Download the replacement result",
        data=download_data,
        file_name="replacement_result.html",
        mime="text/html"
    )

st.write("---")

#=================================================================
# ページ下部に、アプリのGitHubリポジトリのリンクを表示
#=================================================================
st.title("GitHub Repository for This App")
st.markdown("https://github.com/TakafumiYamauchi/Esperanto-Kanji-Converter-and-Ruby-Annotation-Tool-English")

