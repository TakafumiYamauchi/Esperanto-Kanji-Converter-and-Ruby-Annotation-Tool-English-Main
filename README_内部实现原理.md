# Esperanto-Kanji-Converter-and-Ruby-Annotation-Tool-English

Below is an **in-depth technical guide** intended for **intermediate-level Python/Streamlit developers** who already have a basic idea of the GUI usage but want a **deep dive** into how the codebase itself works. We will explore the **core architecture**, **data flow**, **module interactions**, and the **logic** behind the app’s functionality. This guide covers:

1. **Overall App Structure**  
2. **`main.py`: The Primary Streamlit Application**  
3. **`JSON File Generation Page for Esperanto Text (Kanji) Replacement.py`: The Secondary (Pages) Module**  
4. **`esp_text_replacement_module.py`: Replacement Logic & Multiprocessing**  
5. **`esp_replacement_json_make_module.py`: JSON-Building & Word-Stemming Logic**  
6. **Key Techniques & Considerations** (e.g., placeholders, morphological expansions, concurrency)

---

## 1. Overall App Structure

The repository comprises four main Python files that form a Streamlit application. Two of these (`main.py` and `JSON File Generation Page for Esperanto Text (Kanji) Replacement.py`) are **entry points** as Streamlit pages, while the other two (`esp_text_replacement_module.py` and `esp_replacement_json_make_module.py`) provide **shared modules** of logic. Here’s the top-level overview:

- **`main.py`**  
  This is the **primary** Streamlit script. It handles:
  - UI for users to upload or select a JSON file containing replacement rules.
  - Text input (manual or file-upload).
  - Calls to the replacement logic (in the imported modules) to process that text (i.e., apply the Kanji or ruby transformations).
  - Parallel processing setup (using Python’s `multiprocessing` with a custom “spawn” method).
  - Display and download of the final replaced text.

- **`JSON File Generation Page for Esperanto Text (Kanji) Replacement.py`**  
  A separate Streamlit “page” that:
  - Allows advanced users to **generate** or **customize** the large replacement JSON itself.
  - Merges data from user-provided CSV and JSON to produce a combined set of rules.
  - Outputs a JSON with three main arrays (for global replacements, local-only replacements, and 2-char root expansions).

- **`esp_text_replacement_module.py`**  
  A **utility** module that provides:
  - Esperanto character transformations (e.g., from `cx` → `ĉ`, or from `c^` → `ĉ`, etc.).
  - Functions to handle placeholders (for skipping `%...%` or local-only `@...@` replacements).
  - The main orchestration function (`orchestrate_comprehensive_esperanto_text_replacement`) that actually performs multi-step replacements on text.
  - A parallel-processing approach (`parallel_process`) that can break text into lines and handle them across multiple processes.

- **`esp_replacement_json_make_module.py`**  
  Another **utility** module used mostly in the JSON generation workflow. It includes:
  - Additional transformations related to **word-stemming** or morphological expansions (particularly for Esperanto suffixes/prefixes).
  - Functions for measuring text width (so that if the ruby text is significantly longer than the main text, it adjusts the style).
  - Functions to build the combined JSON dictionary from raw CSV/JSON data, with special priority logic for multi-character roots.

Essentially, the two `.py` modules do the heavy lifting behind the scenes, while the two **Streamlit scripts** (`main.py` and `JSON File Generation Page...py`) provide the user interface.

---

## 2. `main.py`: The Primary Streamlit Application

### 2.1 Imports & Setup
```python
import streamlit as st
import multiprocessing
import json
# ...
from esp_text_replacement_module import (
    x_to_circumflex,
    x_to_hat,
    hat_to_circumflex,
    ...
    orchestrate_comprehensive_esperanto_text_replacement,
    parallel_process,
    apply_ruby_html_header_and_footer
)
```
- Notable is the `multiprocessing.set_start_method("spawn")` block. On some platforms, especially in Streamlit Cloud or Windows, this ensures stable parallelism without `PicklingError`.

- We also see a `@st.cache_data` decorator in `load_replacements_lists()`. This caches the loaded JSON so that re-runs don’t repeatedly parse large JSON files.

### 2.2 Page Configuration
```python
st.set_page_config(page_title="Esperanto Text (Kanji) Replacement Tool", layout="wide")
```
Streamlit’s built-in function sets the page’s browser tab title and layout mode to “wide”.

### 2.3 Loading the Replacement JSON
The user is prompted to either:
1. **Use the default JSON**, loaded from a path in the repository.
2. **Upload** a JSON file via file-uploader.

When the JSON is loaded successfully, three lists are extracted:

- `replacements_final_list`  
  The big global replacement list, e.g., `("kanto", "<ruby>kanto<rt>someKanji</rt></ruby>", "somePlaceholder")`.
- `replacements_list_for_localized_string`  
  This is used if the user encloses text in `@...@`.
- `replacements_list_for_2char`  
  This deals specifically with short (two-character) Esperanto roots or suffixes like `-ad, -as, -is`, etc.

### 2.4 Placeholders for Skipping & Localized Replacement
```python
placeholders_for_skipping_replacements = import_placeholders(...txt)
placeholders_for_localized_replacement = import_placeholders(...txt)
```
- These come from text files listing unique placeholder strings. The reason is that we do a two-phase or multi-phase replacement approach:  
  1. Replace the old substring with a unique placeholder that **does not** appear in normal text.  
  2. Then replace that placeholder with the final new substring.  
- This technique **avoids** collisions, e.g., accidentally re-replacing already replaced text.

### 2.5 Advanced Settings: Parallel Processing
```python
use_parallel = st.checkbox("Enable parallel processing", value=False)
num_processes = st.number_input("Number of parallel processes", min_value=2, max_value=4, ...)
```
- If parallel processing is enabled, the text replacement is carried out by splitting the user’s input text into lines, distributing them among multiple processes, and merging the results.

### 2.6 Input Text
We see two main options:
- Manual text in a `st.text_area`
- File upload (`st.file_uploader`)

### 2.7 The Replacement Process
When the user clicks **Submit**, the core logic is:
```python
if use_parallel:
    processed_text = parallel_process(
        text=text0,
        num_processes=num_processes,
        ...
    )
else:
    processed_text = orchestrate_comprehensive_esperanto_text_replacement(
        text=text0,
        ...
    )
```
**`orchestrate_comprehensive_esperanto_text_replacement()`** is the all-in-one function that:

1. Normalizes spaces.  
2. Converts `cx`, `c^`, etc. to the unified form `ĉ`.  
3. Temporarily replaces anything inside `%...%` with placeholders so it’s **skipped** from Kanji transformations.  
4. Temporarily processes anything inside `@...@` using a localized replacement list.  
5. Applies the big global replacement list to the entire text.  
6. Applies the 2-char root replacement (potentially in multiple passes).  
7. Restores placeholders back into the final text.  
8. If the format is HTML-based, it does some post-processing (like converting newlines to `<br>` and turning multiple spaces into `&nbsp;` sequences).

**`parallel_process()`** does the same but splits the input text line by line among multiple processes. Each chunk is run through `orchestrate_comprehensive_esperanto_text_replacement()` in parallel, then results are joined.

### 2.8 Final Output
After processing, the script:
- Potentially modifies the text again for Esperanto letter output style (like `cx` or `c^`).
- Calls `apply_ruby_html_header_and_footer(processed_text, format_type)`, which might wrap the text in `<html>` + `<style>` + `</html>` if the user wants an advanced HTML style for the ruby annotations.
- Shows the **preview** in tabs.  
- Provides a **Download** button to get the result file (`replacement_result.html` or so).

---

## 3. `JSON File Generation Page for Esperanto Text (Kanji) Replacement.py`

This file is placed in the `pages/` folder typical of Streamlit’s multi-page setup. It’s a separate UI that advanced users can open from the sidebar. Its goal is to produce a large JSON combining:

- “Global Replacement” rules
- “2-character root” rules
- “Localized” or partial replacement rules

### 3.1 The Flow
1. **User picks/loads a CSV** with `[Esperanto root, Kanji or other translations]`.
2. **User picks/loads** one or two JSON files that define custom word-stemming or custom replacement items.
3. Possibly configures parallel processing.  
4. Hits **“Create the replacement JSON file”**.  
5. The code merges it all, performing morphological expansions (like “root + as”, “root + an” etc.).  
6. The final structure is dumped into a single JSON. The user can download that to then feed into `main.py`.

### 3.2 Core Logic
The critical function is triggered by:
```python
if st.button("Create the replacement JSON file"):
    # ...
```
Inside, you’ll see it do:
- **Load** a massive dataset (`E_stem_with_Part_Of_Speech_list`, `E_roots`, etc.) from local JSON/TXT.  
- Build a dictionary mapping each Esperanto root to a “replacement” form.  
- Sort them by priority (longer strings first to avoid partial overshadowing).  
- Insert placeholders so that the final list is of the form `(old_string, new_string, placeholder)`.  
- For suffix/prefix expansions, it references:

  ```python
  suffix_2char_roots=['ad','ag','am',...]
  prefix_2char_roots=['al','am','av',...]
  standalone_2char_roots=['al','ci','da',...]
  ```

- If the user has a custom JSON for morphological rules, e.g., “verbo_s1” that means “attach the endings `-as, -is, -os`,” it does that.  
- If the user has a custom “replacement items” JSON, it merges those overrides.  
- Finally, it forms three arrays in the final JSON:
  1. `replacements_final_list`
  2. `replacements_list_for_2char`
  3. `replacements_list_for_localized_string`

Hence, the output JSON is structured as:
```json
{
  "全域替换用のリスト(列表)型配列(replacements_final_list)": [...],
  "二文字词根替换用のリスト(列表)型配列(replacements_list_for_2char)": [...],
  "局部文字替换用のリスト(列表)型配列(replacements_list_for_localized_string)": [...]
}
```
This file can be multiple MB in size. The user can then click the “Download” button. That’s the end of the generation process.

---

## 4. `esp_text_replacement_module.py`: Replacement Logic & Multiprocessing

This module is imported by `main.py`. It defines:

1. **Dictionaries** for Esperanto character transformations:
   ```python
   x_to_circumflex = { 'cx': 'ĉ', 'gx': 'ĝ', ... }
   hat_to_circumflex = { 'c^': 'ĉ', ... }
   # etc.
   ```
   The same approach is repeated for going from `ĉ` → `cx` or `ĉ` → `c^`, etc.

2. **`replace_esperanto_chars(text, char_dict)`**  
   A helper that straightforwardly does `text.replace(original, converted_char)` for each pair in `char_dict`.

3. **`safe_replace(text, replacements: List[Tuple[str, str, str]])`**  
   This is the multi-step approach for (old → placeholder) then (placeholder → new). It prevents partial conflicts or repeated replacements.

4. **Placeholder detection** for `%...%` and `@...@`:  
   - `find_percent_enclosed_strings_for_skipping_replacement()`
   - `find_at_enclosed_strings_for_localized_replacement()`
   - These let you do “skip blocks” or “local blocks” of replacement.

5. **`orchestrate_comprehensive_esperanto_text_replacement()`**  
   The **heart** of the entire replacement pipeline:
   - Normalizes halfwidth spaces.
   - Converts to “circumflex” style (if desired).
   - Temporarily replaces `%...%` blocks so they remain intact.
   - Temporarily replaces `@...@` blocks with partial rules.
   - Applies global replacement list (the “(old, new, placeholder)” style).
   - Applies 2-char root list. Possibly does it in multiple passes.
   - Restores placeholders for `%...%` and `@...@`.

6. **`parallel_process()`**  
   Splits input text by lines, uses `multiprocessing.Pool(...).starmap(...)` to apply `process_segment()` on each chunk. Then merges results.  
   `process_segment()` basically calls the main orchestration function on its portion of the lines.

7. **`apply_ruby_html_header_and_footer()`**  
   If the user wants an HTML/ruby-based output, wraps the result in a `<style>` block or `<ruby>` CSS to control the size/position of the annotation text.

In short, `esp_text_replacement_module.py` is **the** engine for the actual text transformations and concurrency.

---

## 5. `esp_replacement_json_make_module.py`: JSON-Building & Word-Stemming Logic

Similarly, this module is imported by the “JSON File Generation Page.” Its responsibilities:

1. **Redundant** or parallel definitions for x→circumflex dictionaries. (You’ll see repeated code from `esp_text_replacement_module.py`. They each have some overlap, likely for organizational convenience.)

2. **Text Width Calculation**:
   ```python
   def measure_text_width_Arial16(text, char_widths_dict: Dict[str, int]) -> int:
       total_width = 0
       for ch in text:
           char_width = char_widths_dict.get(ch, 8)
           total_width += char_width
       return total_width
   ```
   Then `insert_br_at_half_width` or `insert_br_at_third_width` can break the text with `<br>` if the ruby text is significantly longer/shorter than the main text.

3. **`output_format(main_text, ruby_content, format_type, char_widths_dict)`**  
   This produces the snippet (HTML or parentheses style) that merges the main text with a smaller annotation. For example, if `format_type` is `'HTML格式_Ruby文字_大小调整'`, it might do:
   ```html
   <ruby>main_text<rt class="M_M">ruby_content</rt></ruby>
   ```
   with different classes if the ratio of text widths is large or small.

4. **`parallel_build_pre_replacements_dict()`**  
   Another parallel function that processes big lists of roots. It uses `process_chunk_for_pre_replacements()` to do safe_replace in chunks.

5. **Sizable logic** around morphological expansions, e.g., **applying suffix `-as, -is, -os`** for verbs, or `-an, -on` for nouns/adjectives. This is done by scanning dictionaries like `verb_suffix_2l = {'as':'as','is':'is','os':'os',...}`.  
   The code attempts to generate all possible forms of an Esperanto root, set priorities, then store them in the final global replacement list.

6. The final step typically is:
   ```python
   combined_data = {
     "全域替换用のリスト(列表)型配列(replacements_final_list)": replacements_final_list,
     "二文字词根替换用のリスト(列表)型配列(replacements_list_for_2char)": replacements_list_for_2char,
     "局部文字替换用のリスト(列表)型配列(replacements_list_for_localized_string)": replacements_list_for_localized_string
   }
   download_data = json.dumps(combined_data, ensure_ascii=False, indent=2)
   st.download_button(...)
   ```

This means each dictionary entry is turned into an array of tuples, eventually forming the final JSON structure the main page can parse.

---

## 6. Key Techniques & Considerations

1. **Use of Placeholders**  
   The reason for `(old → placeholder → new)` is to ensure no substring that was already replaced will get re-caught in subsequent replacements. This is especially critical in morphological expansions where part of a newly introduced substring might match another pattern.

2. **Multipart Replacements**  
   Because Esperanto can have “root + suffix + suffix + infix,” the code carefully organizes expansions by **priority** (longer strings first, or user-defined integer priority). This prevents short matches from overshadowing a more complete form.

3. **Parallelism**  
   - The app uses Python’s standard `multiprocessing.Pool` with the spawn method.  
   - For large text input, line-based distribution is quite effective.  
   - The user can control concurrency in both pages (the main page for text replacement, or the JSON generation page if building the large dictionary is slow).

4. **Ruby Format Variation**  
   The code sets up multiple “format_type” enumerations (HTML, parentheses, text-only). This approach is done by calling `output_format(main_text, ruby_content, format_type, char_widths_dict)`. So when building the final dictionary, you choose whether `kanto` becomes `<ruby>kanto<rt>某汉字</rt></ruby>` or just `kanto(某汉字)` or even replace the entire text with “某汉字” only.

5. **Large File I/O**  
   Some JSON files can be ~50MB. Because of that, there are frequent references to caching (`@st.cache_data`) and warnings to the user if they do not provide the file or if an error occurs.

6. **Heavily Customized**  
   Notice the code also references many advanced morphological or lexical expansions for Esperanto. That’s not purely a simple dictionary approach—rather, it can handle partial roots, suffixes/prefixes, case variations (capitalization, uppercase, etc.), and skip logic for special blocks.

---

## Conclusion

- The **backbone** of this application is the multi-step text replacement approach in `esp_text_replacement_module.py`.
- The **main** script (`main.py`) provides a user-facing interface to load the big JSON and run the replacements on user-supplied text, optionally in parallel.
- The **secondary** Streamlit page (`JSON File Generation Page...py`) merges external data (CSV + optional custom JSONs) to **build** that big JSON, leveraging morphological expansions and suffix logic from `esp_replacement_json_make_module.py`.
- Both `.py` **modules** heavily rely on placeholders, safe replacements, substring priority, and morphological expansions, reflecting a robust solution to a complicated multi-script transformation problem (Esperanto → Kanji + ruby).

For an **intermediate programmer** exploring or extending this code:
- Familiarize yourself with the **placeholder** pattern, as it’s central to safe replacements.  
- Understand the **priority** sorting (longest match first) so that morphological expansions override shorter partial matches.  
- Note how `parallel_process()` chunks the text for concurrency. If you want to adapt it for your environment, watch for the `spawn` method and potential pickling constraints.  
- If you plan to add new morphological expansions or custom translations, you can either:
  1. **Edit** the CSVs or custom JSON, then rebuild the combined JSON in the generation page.  
  2. Directly append your new rules into the final JSON arrays.  

**This completes the deep-dive into the codebase**. By understanding these interactions—**especially** the interplay of placeholders and morphological expansions—you can confidently modify, debug, or expand the system to suit new script conversions or advanced linguistic features.
