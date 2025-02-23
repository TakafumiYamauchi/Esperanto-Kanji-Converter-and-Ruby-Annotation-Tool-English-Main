# Esperanto-Kanji-Converter-and-Ruby-Annotation-Tool-English

---
Below is a **comprehensive English-language manual** intended for **GUI users in an English-speaking context**. It explains, in detail, how to use this Streamlit app—which consists of multiple Python files—to convert Esperanto text into a Kanji-enhanced version with optional ruby (furigana) annotations.

---
# Part 1: Overview

This Streamlit application provides two main functionalities, each accessible on separate pages within Streamlit:

1. **Main App Page** (`main.py`)  
   - This is the primary interface for performing **Esperanto text (Kanji) replacement** and optional **ruby (furigana) annotations** on any text you supply. You can:
     - Load or upload a custom JSON file that defines the replacement rules.
     - Input or upload the text you want to process.
     - Choose the output format (HTML with ruby, parentheses style, etc.).
     - Retrieve your processed output (including a download button).

2. **JSON File Generation Page** (`JSON File Generation Page for Esperanto Text (Kanji) Replacement.py`)  
   - This is an **advanced/optional page** for those who want to **create or customize** the big replacement-rule JSON file themselves. If you do not want to create a custom JSON file, you can simply rely on the default JSON in the main page.
   - By merging CSV-based data (Esperanto roots → translations) and custom morphological rules, it produces a large, combined JSON file. This JSON includes:
     1. **Global replacement list** (used by main.py to do standard replacements).
     2. **2-character root replacement list** (for short prefix/suffix roots).
     3. **Localized replacement list** (for text enclosed in `@...@`).

---

# Part 2: Main Page Usage (`main.py`)

### 2.1 Purpose
On the **main** page, you can take an Esperanto text (containing any subset of words, phrases, or paragraphs) and **replace** parts of it with Kanji or other script, optionally with a ruby-like annotation. This allows for:

- **Bilingual or multi-script text**: e.g., “Esperanto word (with Kanji) + small annotation on top.”
- **Previewing the replaced text** in HTML format or in other stylings (parentheses, text only, etc.).
- **Downloading** the processed text as an HTML file.

### 2.2 Accessing the Page
When you launch the Streamlit app (for example, on Streamlit Cloud or locally), you will see a sidebar or navigation menu. The default page is typically the “main” page. The title displayed is:

> **Extended Tool for Replacing Esperanto Text with Kanji and Adding Ruby Annotations**

### 2.3 Steps to Use the Main Page

1. #### Select or Upload Your Replacement JSON
   Near the top, you’ll be prompted:
   > *How would you like to load the replacement JSON file?*  
   You have two options:
   - **Use the default JSON file**: If you don’t have a customized file, pick this. The app loads a default, pre-merged JSON behind the scenes.
   - **Upload a JSON file**: If you already generated a custom JSON using the “JSON File Generation Page” or have your own, you can upload it here.

   There’s also an **expander** labeled **"Sample JSON (Replacement JSON file)"**, inside which you can download a **sample** if you wish to see the format.

2. #### (Optional) Parallel Processing Settings
   You’ll see a section labeled **“Advanced Settings (Parallel Processing)”**.  
   - If you want to process very large input texts more quickly, you can enable **Enable parallel processing** and then specify the **Number of parallel processes** (2–4).  
   - By default, parallel processing is **off**. Most typical texts are processed very fast even without parallelization, but large texts may benefit from it.

3. #### Choose Output Format
   A dropdown labeled **"Choose the output format..."** provides multiple styles for the processed text, including:
   - **HTML Ruby with size adjustment**  
     (Shows the Esperanto word with a “ruby” of Kanji or vice versa, automatically adjusting the font size so that longer rubies are shrunk more.)
   - **HTML Ruby with size adjustment + Kanji replacement**  
     (Same as above, but the main text is Kanji and the smaller annotation is the original Esperanto.)
   - **HTML format only**  
     (Straight ruby annotation, but no special size scaling.)
   - **HTML format + Kanji replacement**
   - **Parentheses format**  
     (Displays the new text as `EsperantoWord(Kanji)`.)
   - **Parentheses format + Kanji replacement**  
     (Displays as `Kanji(EsperantoWord)`.)
   - **Replace with Kanji (no markup), text only**  
     (Simply replaces the Esperanto text with the corresponding Kanji or other script, with no parentheses or HTML markup.)

4. #### Provide Input Text
   You can supply the text to be processed in either of two ways:
   - **Manual entry**: A text area to type or paste your Esperanto text.  
   - **File upload**: If you prefer, you can upload a `.txt`, `.csv`, or `.md` file containing your text.

5. #### Using Special Syntax for Skips and Local-Only Replacement
   - **Skip** a portion of text from replacement by wrapping it with `%...%`. For instance, `%JenNoChange%` means the part `JenNoChange` remains untouched in the final output.  
   - **Local-Only** replacement with `@...@`:  
     If you specifically wrap something with `@...@`, only that enclosed portion is replaced with Kanji, and everything else is not replaced (except for globally replaced words that occur outside the `@...@` block).

6. #### Configure Esperanto Special Characters Output
   A small section asks:
   > *Choose the output style for special Esperanto characters:*  
   - **Use superscript notation**: e.g., `ĉ` → `cx` but stylized with a caret or circumflex.  
   - **Use x notation**: e.g., `ĉ` becomes `cx`.  
   - **Use ^ notation**: e.g., `ĉ` becomes `c^`.

7. #### Click Submit (or Cancel)
   - **Submit**: The app processes your text using the selected JSON rules and displays your replaced text.  
   - **Cancel**: Aborts the current operation.

8. #### View and Download the Results
   - The app shows the processed text in a **tab or text area**. If you chose an HTML-based format, you get:
     - **HTML Preview** (a live rendering)  
     - **Replacement Result (HTML source)** (the raw HTML code)
   - If the text is extremely long, the preview may show only partial lines, but the **download** file will contain the full result.
   - Use the **Download button** to get an `.html` (or `.txt`) output that you can open or save locally.

9. #### GitHub Link
   At the bottom, there is a link to the **GitHub repository** for this app if you wish to see the code or contribute.

---

# Part 3: JSON File Generation Page
_File: `JSON File Generation Page for Esperanto Text (Kanji) Replacement.py`_

### 3.1 Purpose
This second page is designed for **advanced** or **power** users who wish to:

- **Create or customize** the large JSON file that the main page uses for the replacement rules.
- Merge several data sources, such as:
  - CSV files mapping **Esperanto roots** to Kanji/English translations.
  - JSON files containing **custom morphological rules** (for advanced word-stemming or specialized replacements).
- Automatically produce a single “merged replacement JSON” that you can then **download** and use in the main page.

If you do **not** need custom rules or your own CSV, you can skip this page. The main page has a default JSON that suffices in many cases.

### 3.2 How It Works
The page implements these steps internally:

1. **Load CSV**: (Esperanto root → Kanji or other translations).  
2. **Load Word-Stemming Rules (JSON)**: (Custom ways to break down a root or combine suffixes).  
3. **(Optional) Load Additional Replacement Strings (JSON)**.  
4. **Combine** all the above to produce three arrays in one big JSON:
   1. **Global replacement list** (long list, used for standard word replacements),
   2. **2-character root replacement list** (for short suffixes/prefixes),
   3. **Localized replacement list** (used specifically for text enclosed in `@...@` in the main app).

### 3.3 Steps to Use the Generator Page

1. **CSV File Choice**  
   - Decide whether to **upload** your own CSV or **use the default**.  
   - This CSV typically has two columns: `[Esperanto root, translation (Kanji, English, etc.)]`.  

2. **Word-Stemming JSON File Choice**  
   - Again, you can **upload** or **use the default**.  
   - This JSON file can specify how to handle certain morphological expansions, e.g., if you want “am” to always be recognized as a verb root, plus standard endings.  

3. **Additional Replacement Strings JSON**  
   - Optionally, you can also specify custom per-word overrides.  
   - If you do not have any specialized overrides, select the default.

4. **Advanced Settings (Parallel Processing)**  
   - If the CSV is large, you can enable multiple processes.

5. **Click “Create the replacement JSON file”**  
   - The app merges everything, performing expansions such as “word + ‘as’” for verbs, or dealing with short suffixes like `-ad`, `-ig`, `-in`, etc.  
   - It then **generates** a new JSON with three lists inside:  
     - `"全域替换用のリスト(列表)型配列(replacements_final_list)"`  
     - `"二文字词根替换用のリスト(列表)型配列(replacements_list_for_2char)"`  
     - `"局部文字替换用のリスト(列表)型配列(replacements_list_for_localized_string)"`  
   - A download button appears, letting you save this final combined JSON file locally.

6. **Use the Generated JSON on the Main Page**  
   - After downloading the merged JSON, return to the **main page** (`main.py`), choose **Upload a JSON file**, and select the newly generated file to apply your custom rules.

---

# Part 4: Key Tips & Notes

1. **Large Files**:  
   - The combined JSON can be quite large (tens of MB). If performance becomes slow, consider enabling parallel processing in both the generation page and the main page.

2. **Reserved Syntax**:  
   - `%text%` → Protects `text` from **any** replacement.
   - `@text@` → Restricts replacement to `text` only. (This localized block is processed using the special list in the JSON.)

3. **Esperanto Special Characters**:  
   - The app can handle `ĉ, ĝ, ĥ, ĵ, ŝ, ŭ` and their uppercase forms. In the final output, you can choose whether to display them as `cx, c^, Ĉ, etc.`

4. **Parallel Processing**:  
   - Parallelization is typically done **line by line**. If your input text is huge, splitting the work across multiple processes can speed things up.

5. **Download Buttons**:  
   - The app’s “Download” button in Streamlit might produce a file named something like `replacement_result.html` or `final replacement list (merged 3 JSON files).json`.  
   - You can rename it locally as desired.

6. **Possible Conflicts**:  
   - If you have special morphological expansions in your custom JSON, you might see unexpected results. (Example: a suffix “an” might conflict with “Amerikan.”)  
   - The advanced generation code tries to handle these via priorities and carefully merges items, but in unusual edge cases, you may need to tweak or remove certain entries in your CSV/JSON.

7. **Where to Get the Sample Files**:  
   - In the “JSON File Generation Page,” an expander labeled **“Sample Files for Download”** offers sample CSVs and JSONs that illustrate the expected data format.

---

# Part 5: Frequently Asked Questions (FAQ)

1. **Q**: Can I skip using the “JSON File Generation Page”?  
   **A**: Yes. You can simply use the default JSON on the main page. The generation page is only if you want a very **tailored** set of replacement rules or want to merge your own dictionary data.

2. **Q**: Why does the output HTML show `<ruby>...<rt>...</rt></ruby>` tags?  
   **A**: That’s the standard way to display “ruby text” (like furigana) in HTML. Modern browsers typically support it well. If you prefer parentheses or no markup, select a different output format in the main page.

3. **Q**: My output text is extremely long, and I only see part of it in the preview. Where is the rest?  
   **A**: Streamlit sometimes truncates preview for very large strings. But the **downloaded file** is complete.

4. **Q**: My text includes numeric digits or punctuation. Will they cause errors in the replacement?  
   **A**: Typically no. The code primarily targets alphanumeric + Esperanto letters. Digits or punctuation do not get replaced unless explicitly defined in your CSV/JSON.

5. **Q**: How do I handle an error “Failed to load the JSON file” in the main page?  
   **A**: Double-check the file you uploaded is a valid `.json` with the correct structure. Possibly the JSON is corrupted or not in UTF-8. Also confirm you are not mixing up the large “combined JSON” with other file types.

6. **Q**: What if the Kanji translation is identical to the original Esperanto root?  
   **A**: Then the code may skip or treat them as duplicates. In many cases, it merges them. But if you see something undesired, consider removing or editing that entry in your CSV or JSON.

---

# Part 6: Conclusion

This Streamlit application is quite **powerful** for those who want to experiment with **multi-script** or **Kanji-based** rendering of Esperanto text. You can use it **immediately** with the **default** rules on the **main** page, or **dig deeper** into morphological expansions, suffix handling, and specialized glosses by customizing the JSON generation in the **second page**.

**Recommended usage**:
1. Start with the **main page**. Upload or use the default JSON. Try a short Esperanto text and see how the tool transforms it.
2. If you feel comfortable and want a specialized dictionary (for example, your own Kanji mappings or English rubies), proceed to the **“JSON File Generation Page”** to combine your CSV data with the morphological rules, then produce a new merged JSON to load on the main page.

Enjoy exploring Kanji-based or multi-script transformations of Esperanto, and feel free to check out the **GitHub repository** for further details or code contributions.

---

> **We hope this manual provides a clear and thorough guide.**  
> **For questions or troubleshooting**, check the built-in help text on each page’s **expander** sections or consult the code on GitHub.  

**End of Manual**  
