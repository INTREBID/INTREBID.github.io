# 从原网站匹配论文条目，并下载PDF
# https://www.ruizhang.info/
# https://dblp.org/pid/03/505.html?view=bibtex
# 1. 从网站上获取论文条目
# 2. 从本地bib文件(dblp ruizhang003)中获取论文条目
# 3. 匹配论文条目，并下载PDF,并匹配会议期刊的shortname
# 4. 保存匹配结果

import requests
from bs4 import BeautifulSoup
import bibtexparser
import re
import os
from urllib.parse import urljoin
from difflib import SequenceMatcher
from tqdm import tqdm

def load_bib_entries(bib_file):
    with open(bib_file, 'r', encoding='utf-8') as f:
        bib_database = bibtexparser.load(f)
    return bib_database.entries

def download_pdf(url, filename, pdf_dir):
    """
    下载PDF文件，如果本地已存在则跳过

    Args:
        url: PDF文件的URL
        filename: 保存的文件名（不含扩展名）
        pdf_dir: PDF文件保存目录

    Returns:
        bool: 下载是否成功（包括已存在的情况）
    """
    if not filename:
        return False

    # 替换文件名中的斜杠为下划线，并处理已有的下划线
    filename = filename.replace('\\_', '_')
    local_path = os.path.join(pdf_dir, f"{filename}.pdf")

    # 检查文件是否已存在
    if os.path.exists(local_path):
        print(f"PDF already exists: {filename}.pdf")
        return True

    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            with open(local_path, 'wb') as f:
                f.write(response.content)
            print(f"Downloaded: {filename}.pdf")
            return True
        else:
            print(f"Failed to download {filename}.pdf: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"Error downloading {filename}.pdf: {str(e)}")
        return False

def extract_doi_from_url(url):
    doi_patterns = [
        r'10\.\d{4,}/[-._;()/:\w]+',
        r'doi\.org/(.+)$'
    ]
    for pattern in doi_patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(0)
    return None

def normalize_title(title):
    """
    规范化标题：
    1. 转换为小写
    2. 只保留字母和数字，其他所有字符都替换为空格
    3. 分词并用单个空格重新连接
    """
    if not title:
        return ""

    # 转换为小写
    title = title.lower()

    # 将所有非字母数字字符替换为空格
    # [^a-z0-9] 表示匹配任何不是小写字母或数字的字符
    title = re.sub(r'[^a-z0-9]+', ' ', title)

    # 分词并用单个空格重新连接
    words = title.split()
    title = ' '.join(words)

    return title

def fuzzy_match_title(title1, title2, threshold=0.85):
    """
    使用规范化后的标题进行模糊匹配
    """
    # 规范化两个标题
    norm_title1 = normalize_title(title1)
    norm_title2 = normalize_title(title2)

    # 如果规范化后的标题完全相同
    if norm_title1 == norm_title2:
        return True

    # 使用序列匹配器计算相似度
    similarity = SequenceMatcher(None, norm_title1, norm_title2).ratio()

    # 调试信息（可选）
    # if similarity > 0.5:  # 只打印相似度较高的匹配结果
    #     print(f"\nMatching titles:")
    #     print(f"Original 1: {title1}")
    #     print(f"Original 2: {title2}")
    #     print(f"Normalized 1: {norm_title1}")
    #     print(f"Normalized 2: {norm_title2}")
    #     print(f"Similarity: {similarity}")

    return similarity >= threshold

def extract_title_from_font(font_element):
    """
    从font元素中提取论文标题：
    1. 如果存在a标签，使用a标签的文本作为标题
    2. 如果不存在a标签，使用倒数第二个逗号和最后一个逗号之间的内容作为标题
    """
    if not font_element:
        return None

    # 首先查找a标签
    a_tag = font_element.find('a')
    if a_tag:
        return a_tag.get_text().strip()

    # 如果没有a标签，使用逗号分隔法
    contents = [str(content) for content in font_element.contents]
    text = ''.join(contents)

    # 找到所有逗号的位置
    comma_positions = [i for i, char in enumerate(text) if char == ',']

    # 确保至少有两个逗号
    if len(comma_positions) < 2:
        return None

    # 获取倒数第二个和最后一个逗号的位置
    last_comma = comma_positions[-1]
    second_last_comma = comma_positions[-2]

    # 提取标题并清理
    title = text[second_last_comma + 1:last_comma].strip()

    return title


def write_bibtex_entry(file, entry):
    """写入单个 BibTeX 条目到文件，key占15个字符（包括前面的空格），左对齐

    Args:
        file: 文件对象
        entry: BibTeX 条目字典
    """
    # 获取条目类型和ID
    entry_type = entry.get('ENTRYTYPE', '')
    entry_id = entry.get('ID', '')
    file.write(f'@{entry_type}{{{entry_id},\n')

    # 优先字段顺序
    priority_fields = ['author', 'title']
    # 新加的字段（放在最后）
    new_fields = ['pdf', 'shortname']

    def write_field(key, value):
        """写入单个字段，key占15个字符，左对齐"""
        # 格式化key，确保占15个字符，左对齐
        formatted_key = f"{key:<15}"  # key占15个字符

        if '\n' in str(value):
            # 对多行值进行处理
            lines = str(value).split('\n')
            formatted_value = lines[0] + '\n' + '\n'.join(' ' * 18 + line for line in lines[1:])
            file.write(f'{formatted_key}= {{{formatted_value}}},\n')
        else:
            file.write(f'{formatted_key}= {{{value}}},\n')

    # 先写入优先字段
    for field in priority_fields:
        if field in entry:
            write_field(field, entry[field])

    # 写入其他原有字段
    for key, value in entry.items():
        if (key not in priority_fields and
            key not in new_fields and
            key not in ['ENTRYTYPE', 'ID']):
            write_field(key, value)

    # 最后写入新字段
    for field in new_fields:
        if field in entry:
            write_field(field, entry[field])

    file.write('}\n\n')

def replace_special_chars(text):
    """替换特殊字符"""
    text = text.replace('&nbsp;', ' ')
    text = text.replace('\r', ' ')
    text = text.replace('\n', ' ')
    text = text.replace('\t', ' ')
    text = text.replace('¡', '')
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

def extract_shortname_from_element(text, title):
    """提取期刊/会议信息，从title后第一个分隔符（逗号或句号）开始到条目结束
    Args:
        text: 完整文本
        title: 论文标题
    Returns:
        str: 提取的shortname
    """
    if not title or not text:
        return None

    text = replace_special_chars(text)

    # 找到title在文本中的位置
    title_pos = text.find(title)
    if title_pos == -1:
        return None

    # 从title后开始查找第一个逗号或句号
    start_pos = title_pos + len(title)
    text_after_title = text[start_pos:]

    # 找到第一个分隔符（逗号或句号）
    first_separator = None
    for i, char in enumerate(text_after_title):
        if char in [',', '.']:
            first_separator = i
            break

    if first_separator is None:
        return None

    # 从第一个分隔符后开始提取到结束
    venue_text = text_after_title[first_separator + 1:].strip()
    if not venue_text:
        return None

    # 查找所有括号内容
    bracket_matches = re.finditer(r'\((.*?)\)', venue_text)
    for match in bracket_matches:
        bracket_content = match.group(1)
        # 如果括号内容不是纯数字，使用它作为shortname
        if not bracket_content.isdigit():
            # 检查括号内容是否已包含年份
            if re.search(r'\b(19|20)\d{2}\b', bracket_content):
                return bracket_content.strip()
            # 如果没有年份，从整个文本中查找
            year_match = re.search(r'\b(19|20)\d{2}\b', text)
            if year_match:
                return f"{bracket_content.strip()} {year_match.group()}"
            return bracket_content.strip()

    # 检查完整文本是否已包含年份
    if re.search(r'\b(19|20)\d{2}\b', venue_text):
        return venue_text.strip()

    # 如果没有找到非数字的括号内容，返回完整文本（如果需要添加年份）
    year_match = re.search(r'\b(19|20)\d{2}\b', text)
    if year_match:
        return f"{venue_text.strip()} {year_match.group()}"
    return venue_text.strip()

def extract_paperinfo_from_website(pub_element):
    """
    从publication元素中提取标题和shortname：
    1. 获取<li>标签的完整文本用于提取shortname
    2. 从font或span元素中提取标题
    """
    full_text = pub_element.get_text(strip=True) # 获取<li>标签的完整文本

    # 首先尝试从font中提取标题
    font_face = pub_element.find('font')
    if font_face:
        title = extract_title_from_element(font_face)
        if title:
            shortname = extract_shortname_from_element(full_text, title)  # 使用完整文本提取shortname
            return title, shortname

    # 如果font中没有找到，尝试从span中提取标题
    span_element = pub_element.find('span')
    if span_element:
        title = extract_title_from_element(span_element)
        if title:
            shortname = extract_shortname_from_element(full_text, title)  # 使用完整文本提取shortname
            return title, shortname

    return None, None

def extract_title_from_element(element):
    """
    从给定元素（font或span）中提取标题：
    1. 如果存在a标签，使用a标签的文本作为标题
    2. 如果不存在a标签，使用倒数第二个逗号和最后一个逗号之间的内容作为标题
    """
    if not element:
        return None

    # 首先查找a标签
    a_tag = element.find('a')
    if a_tag:
        title = a_tag.get_text().strip()
        title = title.rstrip('.') # 去掉末尾的句号
        title = replace_special_chars(title)
        return title

    # 如果没有a标签，使用逗号分隔法
    contents = [str(content) for content in element.contents]
    text = ''.join(contents)

    comma_positions = [i for i, char in enumerate(text) if char == ',']
    if len(comma_positions) < 2:
        return None

    # 获取倒数第二个和最后一个逗号的位置
    last_comma = comma_positions[-1]
    second_last_comma = comma_positions[-2]

    # 提取标题并清理
    title = text[second_last_comma + 1:last_comma].strip()
    title = replace_special_chars(title)

    return title

def main():
    # 设置路径配置
    base_dir = 'python/'
    pdf_dir = os.path.join('assets', 'pdf')
    rst_dir = os.path.join(base_dir, 'rsts')

    bib_library = os.path.join(base_dir, '505.bib')
    bib_matched = os.path.join("_bibliography", 'papers.bib')

    # 创建必要的目录
    os.makedirs(pdf_dir, exist_ok=True)
    os.makedirs(rst_dir, exist_ok=True)

    # Load existing bib entries
    bib_entries = load_bib_entries(bib_library)

    # Initialize result containers
    matched_with_pdf = []      # Case 1: 匹配到且有PDF
    matched_no_pdf = []        # Case 2: 匹配到但没有PDF
    unmatched_with_pdf = []    # Case 3: 未匹配到但有PDF
    unmatched_no_pdf = []      # Case 4: 未匹配到且没有PDF
    skipped_entries = []       # 跳过条目的列表

    # Scrape website
    base_url = 'https://www.ruizhang.info/publications/'
    url = base_url + 'pubindex.htm'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    publications = soup.find_all('li')[:212]

    matched_entries = []  # 用于按顺序存储匹配的条目

    # Add progress bar
    for pub in tqdm(publications, desc="Processing publications", unit="paper"):
        title,shortname = extract_paperinfo_from_website(pub)
        if not title:
            skipped_entries.append({'html': str(pub), 'title': '{title}', 'shortname': '{shortname}'})
            continue

        # 1. 检查是否有PDF
        pdf_found = False
        pdf_href = None
        links = pub.find_all('a')
        for link in links:
            href = link.get('href', '')
            if href and href.lower().endswith('.pdf'):
                pdf_found = True
                pdf_href = urljoin(base_url, href)
                break

        # 2. 检查是否能匹配到条目
        matching_entry = None
        for entry in bib_entries:
            if fuzzy_match_title(entry.get('title', ''), title):
                matching_entry = entry
                break

        # 3. 根据匹配结果和PDF存在与否分类处理
        if matching_entry:
            if pdf_found:
                # Case 1: 匹配到且有PDF
                filename = matching_entry.get('doi', '') or matching_entry.get('ID', '')
                if download_pdf(pdf_href, filename, pdf_dir):
                    matching_entry['pdf'] = f"{filename}.pdf"
                matching_entry['shortname'] = shortname
                matched_with_pdf.append(matching_entry)
                matched_entries.append(matching_entry)
            else:
                # Case 2: 匹配到但没有PDF
                matching_entry['shortname'] = shortname
                matched_no_pdf.append(matching_entry)
                matched_entries.append(matching_entry)
        else:
            if pdf_found:
                # Case 3: 未匹配到但有PDF
                safe_title = title.lower()  # 转换为小写
                safe_title = re.sub(r'[^a-z0-9\s-]', ' ', safe_title)
                safe_title = ' '.join(safe_title.split())
                safe_title = safe_title.replace(' ', '-')
                safe_title = safe_title[:200]

                download_pdf(pdf_href, safe_title, pdf_dir)
                unmatched_with_pdf.append({'item': str(pub),'pdf': f"{safe_title}.pdf"})
            else:
                # Case 4: 未匹配到且没有PDF
                unmatched_no_pdf.append({'item': str(pub)})

    # 4. 保存结果
    with open(bib_matched, 'w', encoding='utf-8') as f:
        for entry in matched_entries:  # 修改：使用按顺序存储的列表
            write_bibtex_entry(f, entry)

    # 保存统计信息
    with open(os.path.join(rst_dir, 'summary.txt'), 'w', encoding='utf-8') as f:
        f.write("### 统计信息 ###\n")
        f.write(f"总共处理文献数: {len(publications)}\n")
        f.write(f"条目匹配到且网站存在PDF: {len(matched_with_pdf)}\n")
        f.write(f"条目匹配到但网站无PDF: {len(matched_no_pdf)}\n")
        f.write(f"条目未匹配但网站有PDF: {len(unmatched_with_pdf)}\n")
        f.write(f"条目未匹配且网站无PDF: {len(unmatched_no_pdf)}\n")
        f.write(f"跳过条目: {len(skipped_entries)}\n")

    # 保存匹配到但缺少PDF的警告
    if matched_no_pdf:
        with open(os.path.join(rst_dir, 'matched_no_pdf.txt'), 'w', encoding='utf-8') as f:
            f.write("⚠️ 匹配到但缺少PDF的条目:\n\n")
            for entry in matched_no_pdf:
                f.write(f"- Title: {entry.get('title', 'No title')}\n")
                f.write(f"  ID: {entry.get('ID', 'No ID')}\n\n")

    # 保存未匹配但有PDF的警告
    if unmatched_with_pdf:
        with open(os.path.join(rst_dir, 'unmatched_with_pdf.txt'), 'w', encoding='utf-8') as f:
            f.write("❗ 未匹配但存在PDF的条目:\n\n")
            for entry in unmatched_with_pdf:
                f.write(f"- Item: {entry['item']}\n")
                f.write(f"  PDF: {entry['pdf']}\n\n")

    # 保存未匹配且无PDF的警告
    if unmatched_no_pdf:
        with open(os.path.join(rst_dir, 'unmatched_no_pdf.txt'), 'w', encoding='utf-8') as f:
            f.write("❌ 未匹配且无PDF的条目:\n\n")
            for entry in unmatched_no_pdf:
                f.write(f"- Item: {entry['item']}\n\n")

    if skipped_entries:
        with open(os.path.join(rst_dir, 'skipped_entries.txt'), 'w', encoding='utf-8') as f:
            f.write("🚫 跳过条目:\n\n")
            for entry in skipped_entries:
                f.write(f"- Title: {entry['title']}\n")
                f.write(f"  Shortname: {entry['shortname']}\n")
                f.write(f"  HTML: {entry['html']}\n\n")

if __name__ == "__main__":
    main()