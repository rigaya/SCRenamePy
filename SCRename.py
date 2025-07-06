#!/usr/bin/env python3
# SCRename (python) Ver. 6.0

# python 3.7以降
import os
import sys
import time
import re
import datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass

# 定数定義
SEP = "_"
NIND = "#"
CHAR1 = r" :;/'" + r'"-'
CHAR2 = r"　：；／’”－"
CHAR3 = r"!？！～…『』"
CHAR4 = r"([（〔［｛〈《「【＜"
CHAR5 = r")]）〕］｝〉》」】＞"
CHAR6 = r'/:*?!"<>|'
CHAR7 = r"／：＊？！”＜＞｜"
CHAR8 = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
CHAR9 = ["quot", "amp", "#039", "lt", "gt"]
CHAR10 = ["\"", "&", "'", "＜", "＞"]
CHAR11 = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

@dataclass
class RenameOptions:
    """リネームオプションを管理するデータクラス"""
    test_mode: bool = False        # -t オプション: テストモード
    require_subtitle: bool = False # -n オプション: サブタイトル必須
    force_rename: bool = False     # -f オプション: 強制リネーム
    keep_spaces: bool = False      # -s オプション: 空白を保持
    search_episode: bool = False   # -a オプション: 話数検索
    recursive_search: bool = False # -a1 オプション: 再帰的検索
    start_pos: int = 0            # タイトル開始位置
    search_len: int = 4           # タイトル検索文字数

def get_file_info(file_path: str) -> Tuple[str, str, str]:
    """ファイルパス、ファイル名、拡張子、タイトル開始位置を取得"""
    rpath, filename = os.path.split(file_path)
    if not rpath and len(file_path) >= 2 and file_path[1] == ":":
        rpath = file_path[:2]
    
    # 拡張子の取得
    name, ext = os.path.splitext(filename)
    if SEP in name:
        base, ext2 = os.path.splitext(name)
        if SEP in base and re.match(r'^[0-9a-zA-Z]+$', ext2):
            name = base
    
    return rpath, name, ext

def get_date_from_title(title: str, pos: int) -> Tuple[Optional[datetime.datetime], int, int, int]:
    """タイトルから日付を取得"""
    tgtdt = None
    dtflag = 0
    days = 1
    title_pos = pos  # タイトル開始位置を保持
    
    if len(title) > 8:
        current_year = datetime.datetime.now().year
        for i in range(len(title) - 5):
            if title[i].isdigit():
                j = i + 1
                while j < len(title) and title[j].isdigit():
                    j += 1
                if j - i > 5:
                    year_diff = current_year - int(title[i:i+4])
                    if j - i < 8 or year_diff < -2 or year_diff > 99:
                        date_str = f"{str(current_year)[:2]}{title[i:i+6]}"
                        k = i + 6
                    else:
                        date_str = title[i:i+8]
                        k = i + 8
                    
                    if int(date_str[:4]) < current_year + 3:
                        try:
                            date_str = f"{date_str[:4]}/{date_str[4:6]}/{date_str[6:8]}"
                            tgtdt = datetime.datetime.strptime(date_str, "%Y/%m/%d")
                            if i == 0:  # 日付が先頭にある場合
                                # 日付の長さを計算（YYYYMMDD）
                                date_length = 8
                                # 時間がある場合は追加（HHMM）
                                if k + 4 <= len(title) and title[k:k+4].isdigit():
                                    date_length += 4
                                title_pos = date_length  # タイトル開始位置を日付の次の位置に設定
                            break
                        except ValueError:
                            continue
    
    if title_pos == 0:
        title_pos = 1
    
    if tgtdt and k < len(title) - 2:
        char = title[k]
        if not char.isdigit() and char != SEP:
            k += 1
        if k + 4 <= len(title) and title[k:k+4].isdigit():
            hour = int(title[k:k+2])
            day_add = 0
            if hour > 23:
                hour -= 24
                day_add = 1
            try:
                time_str = f"{hour}:{title[k+2:k+4]}"
                time_obj = datetime.datetime.strptime(time_str, "%H:%M").time()
                tgtdt = tgtdt + datetime.timedelta(days=day_add)
                tgtdt = datetime.datetime.combine(tgtdt.date(), time_obj)
                dtflag = 1
            except ValueError:
                pass
    
    if dtflag == 0 and Path(title).exists():
        file_path = Path(title)
        dt1 = datetime.datetime.fromtimestamp(file_path.stat().st_ctime)
        dt2 = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
        if dt1 < dt2:
            dt2 = dt1
            dtflag = 1
        if not tgtdt:
            tgtdt = dt2
            days = 7
        else:
            tgtdt = datetime.datetime.combine(
                tgtdt.date(),
                datetime.time(dt2.hour, dt2.minute, dt2.second)
            )
    
    if not tgtdt:
        tgtdt = datetime.datetime.now()
    
    return tgtdt, dtflag, days, title_pos

def remove_leading_chars(title: str) -> str:
    """ファイル名先頭部分を削除"""
    
    # 先頭部分記号削除
    i = 0
    while i < len(title):
        char = title[i]
        if char not in SEP + CHAR1 + CHAR2 + CHAR3 + "・":
            j = CHAR4.find(char)
            if j < 0:
                break
            else:
                k = title.find(CHAR5[j], i + 1)
                if k > 0:
                    i = k
                else:
                    break
        elif char == "『":
            k = title.find("』", i + 1)
            if k > 0:
                title = title[:k] + " " + title[k+1:]
        i += 1
        if i >= len(title):
            print(title)
            print("タイトルを取得出来ませんでした。", file=sys.stderr)
            time.sleep(1)
            sys.exit(1)
    
    return title[i:]

def convert_chars(title: str) -> str:
    """全角半角ローマ数字記号変換"""
    result = ""
    for char in title:
        j = CHAR2.find(char)
        if j >= 0:
            result += CHAR1[j]
        else:
            code = ord(char)
            if 0xFF10 <= code <= 0xFF19:  # 全角数字
                result += chr(code - 0xFF10 + ord("0"))
            elif 0xFF21 <= code <= 0xFF3A:  # 全角英大文字
                result += chr(code - 0xFF21 + ord("A"))
            elif 0xFF41 <= code <= 0xFF5A:  # 全角英小文字
                result += chr(code - 0xFF41 + ord("a"))
            elif 0x2160 <= code <= 0x2169:  # ローマ数字
                result += CHAR8[code - 0x2160]
            else:
                result += char
    return result

def get_title(ftitle: str, search_len: int = 4) -> str:
    """タイトルを取得"""
    if search_len < 1:
        search_len = 4
    if search_len > len(ftitle):
        search_len = len(ftitle)
    
    # 最初の文字を取得
    title = ftitle[0]
    
    # search_len文字まで、または区切り文字が見つかるまで文字を追加
    for i in range(1, search_len):
        char = ftitle[i]
        if char in " " + SEP + CHAR3 + CHAR4 + CHAR5:
            break
        title += char
    
    return title

def get_service(ftitle: str, title: str, service: List[List[str]], pos: int) -> int:
    """放送局名を取得"""
    serv = -1
    sep_pos = ftitle.rfind(SEP)
    
    if pos < 7 and sep_pos > 3:
        prev_sep_pos = ftitle.rfind(SEP, 0, sep_pos - 2)
        if prev_sep_pos > 1:
            sep_pos = prev_sep_pos
    
    service_part = ftitle[sep_pos + 1:]
    
    for i in range(4):
        j = 0 if i < 2 else 2
        
        for serv_idx, serv_info in enumerate(service):
            if i in [0, 2]:
                k = service_part.upper().rfind(serv_info[j].upper())
            else:
                k = ftitle.upper().rfind(serv_info[j].upper())
            
            if k >= 0:
                serv = serv_idx
                break
        
        if serv >= 0:
            break
    
    if serv < 0:
        print("放送局が不明のためすべての放送局を対象にします。", file=sys.stderr)
    
    return serv

def search_program_info(html: str, title: str, serv: int, service: List[List[str]], tgtdt: datetime.datetime, dtflag: int) -> Tuple[Optional[str], Optional[str], Optional[int], Optional[datetime.datetime], Optional[datetime.datetime]]:
    """番組情報を検索して取得"""
    # <item>タグ以降を取得
    item_start = html.find("<item>")
    if item_start >= 0:
        html = html[item_start + 6:]
    
    # エスケープ文字の処理
    html = html.replace("\\", "＼")
    
    # HTMLエンティティの処理
    for i in range(len(CHAR9)):
        html = html.replace(f"&{CHAR9[i]};", CHAR10[i])
    
    # 番組情報検索
    pos = 0
    stdt = None
    eddt = None
    
    # タイトルと放送局名で検索
    i = html.find("<title>")
    while i >= 0:
        i += 7
        j = html.find("|", i + 1)
        if j < 0:
            break
        
        if title.upper() in html[i:j].upper():
            k = html.find("|", j + 1)
            if serv < 0:
                j = -1
            elif service[serv][1].upper() in html[j+1:k].upper():
                j = -1
            
            if j == -1:
                # 日付情報の取得
                j = html.find("<pubDate>", k + 1) + 9
                date_str = html[j:html.find("+", j + 10)]
                t_pos = date_str.find("T")
                if t_pos >= 0:
                    date_str = date_str[:t_pos] + " " + date_str[t_pos+1:]
                    try:
                        dt1 = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                        date_str = date_str[:t_pos]
                    except ValueError:
                        dt1 = None
                        date_str = ""
                else:
                    dt1 = None
                    date_str = ""
                
                # 終了時刻の取得
                time_str = date_str + html[k+1:k+6]
                try:
                    dt2 = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                    if dt1 and dt1 >= dt2:
                        dt2 = dt2 + datetime.timedelta(days=1)
                except ValueError:
                    dt2 = None
                
                # 日付の比較
                if dtflag == 1:
                    if not stdt or abs((tgtdt - dt1).total_seconds()) < abs((tgtdt - stdt).total_seconds()):
                        stdt = dt1
                        eddt = dt2
                        pos = i
                else:
                    if not eddt or abs((tgtdt - dt2).total_seconds()) < abs((tgtdt - eddt).total_seconds()):
                        stdt = dt1
                        eddt = dt2
                        pos = i
        
        i = html.find("<title>", i)
    
    # 番組情報取得
    if pos > 0:
        i = html.find("|", pos)
        program_title = html[pos:i]
        j = html.find("|", i + 1)
        
        # 放送局名の取得
        if serv < 0:
            service_name = html[i+1:j]
            for k, serv_info in enumerate(service):
                if serv_info[1] in service_name:
                    serv = k
                    break
            if serv < 0:
                serv = 0
                service[2][0] = service_name
        
        # サブタイトル情報の取得
        i = html.find("|", j + 1)
        j = html.find("</title>", i + 1)
        if i < j - 1:
            subtitle_info = html[i+1:j]
            subtitle = None
            number = None
            part = None
            
            # サブタイトルの解析
            i = subtitle_info.find("「")
            if i > 0:
                if i > 2 and subtitle_info[0] == "#":
                    for j in range(2, i):
                        if subtitle_info[j] == " ":
                            break
                    number = subtitle_info[1:j]
                elif i > 1:
                    part = subtitle_info[:i].strip()
                
                subtitle = subtitle_info[i+1:]
                if subtitle.endswith("」"):
                    subtitle = subtitle[:-1]
            elif subtitle_info.startswith("#"):
                i = 1
                number_parts = []
                subtitle_parts = []
                
                while True:
                    j = subtitle_info.find(" ", i + 1)
                    if j < 0:
                        number_parts.append(subtitle_info[i:])
                        break
                    else:
                        number_parts.append(subtitle_info[i:j])
                        i = subtitle_info.find(" / #", j)
                        if i < 0:
                            if j < len(subtitle_info):
                                subtitle_parts.append(subtitle_info[j+1:].strip())
                            break
                        elif i > j + 1:
                            subtitle_parts.append(subtitle_info[j+1:i-j-1].strip())
                    i += 3
                
                number = ",".join(number_parts)
                if subtitle_parts:
                    subtitle = " ／ ".join(subtitle_parts)
            else:
                part = subtitle_info
            
            if number:
                number = "#" + number
            
            return program_title, subtitle, serv, stdt, eddt, number
    
    return None, None, serv, stdt, eddt, None

def extract_episode_number(title: str) -> Tuple[Optional[int], Optional[str]]:
    """ファイル名から話数を抽出"""
    k = -1
    for i in range(2, len(title) - 2):
        char = title[i]
        if char in "「『":
            break
        elif char in " " + SEP:
            next_char = title[i + 1]
            if next_char in [NIND, "第"]:
                j = i + 2
                while j < len(title) and title[j].isdigit():
                    j += 1
                if j > i + 2:
                    if (next_char == NIND and title[j] in " " + SEP) or (next_char == "第" and title[j] == "話"):
                        k = int(title[i+2:j])
                        break
    
    if k == -1:
        return None, None
    
    # タイトルの取得
    for j in range(2, i):
        if title[j] in SEP + CHAR4 + CHAR5 + "～":
            break
    title = title[:j].rstrip()
    
    return k, title

def get_tid_from_cache(title: str, title2: str) -> Tuple[Optional[int], Optional[str]]:
    """SCRename.tidファイルからTIDを取得"""
    tid_path = os.path.join(os.path.dirname(sys.argv[0]), "SCRename.tid")
    if not os.path.exists(tid_path):
        return None, title
    
    with open(tid_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(",", 1)
            if len(parts) == 2:
                tid_title, tid_id = parts
                if tid_title.replace(" ", "").upper().startswith(title2):
                    print("SCRename.tid から", end="", file=sys.stderr)
                    return int(tid_id), tid_title
    
    return None, title

def search_tid_from_web(title: str, title2: str) -> Tuple[Optional[int], Optional[str]]:
    """しょぼいカレンダーからTIDを検索"""
    encoded_title = urllib.parse.quote(title.encode("utf-8"))
    search_url = f"http://cal.syoboi.jp/find?kw={encoded_title}"
    
    for i in range(3):
        if i > 0:
            time.sleep(1)
        
        try:
            with urllib.request.urlopen(search_url) as response:
                html = response.read().decode("utf-8")
                break
        except Exception as e:
            if i == 2:
                print("\nしょぼいカレンダーにアクセスできませんでした。", file=sys.stderr)
                return None, title
            continue
    
    # HTMLエンティティの処理
    html = html.replace("\\", "＼")
    for i in range(len(CHAR9)):
        html = html.replace(f"&{CHAR9[i]};", CHAR10[i])
    
    # TIDの抽出
    i = len(html)
    while True:
        i = html.rfind("/tid/", 0, i)
        if i < 0:
            break
        
        j = i + 5
        while j < len(html) and html[j].isdigit():
            j += 1
        
        k = int(html[i+5:j])
        j += 2
        l = html.find("</a>", j)
        
        if l > j:
            found_title = html[j:l]
            found_title = found_title.replace("?", "？").replace("!", "！")
            if found_title.replace(" ", "").upper().startswith(title2):
                print("しょぼいカレンダーから", end="", file=sys.stderr)
                return k, found_title
    
    return None, title

def update_tid_cache(tid: int, title: str) -> None:
    """SCRename.tidファイルを更新"""
    tid_path = os.path.join(os.path.dirname(sys.argv[0]), "SCRename.tid")
    
    if os.path.exists(tid_path):
        with open(tid_path, "r", encoding="utf-8") as f:
            tid_data = [line.strip().split(",", 1) for line in f]
    else:
        tid_data = []
    
    # 新しいTIDを挿入
    insert_pos = 0
    for i, (_, tid_id) in enumerate(tid_data):
        if int(tid_id) == tid:
            tid_data[i] = [title, str(tid)]
            break
        elif int(tid_id) > tid:
            insert_pos = i
            break
    else:
        tid_data.insert(insert_pos, [title, str(tid)])
    
    # ファイルに書き込み
    with open(tid_path, "w", encoding="utf-8") as f:
        for tid_title, tid_id in tid_data:
            f.write(f"{tid_title},{tid_id}\n")

def get_program_info_by_tid(tid: int, number: str, serv: int, service: List[List[str]]) -> Optional[str]:
    """TIDを使用して番組情報を取得"""
    service_param = ""
    if serv >= 0 and service[serv][3]:
        service_param = f"&ChID={service[serv][3]}"
    
    print(f"第{number}話{service_param}の情報を検索します。\n", file=sys.stderr)
    
    search_url = f"http://cal.syoboi.jp/db.php?Command=ProgLookup&TID={tid}{service_param}&Count={number}&Fields=StTime,EdTime,ChID,STSubTitle&JOIN=SubTitles"
    
    for i in range(3):
        if i > 0:
            time.sleep(1)
        
        try:
            with urllib.request.urlopen(search_url) as response:
                html = response.read().decode("utf-8")
                break
        except Exception as e:
            if i == 2:
                print("しょぼいカレンダーにアクセスできませんでした。", file=sys.stderr)
                return None
            continue
    
    # 番組情報の解析
    i = html.find("<StTime>")
    if i > 0:
        i += 8
        j = html.find("</StTime>", i)
        date_str = html[i:j].replace("-", "/")
        try:
            stdt = datetime.datetime.strptime(date_str, "%Y/%m/%d %H:%M:%S")
        except ValueError:
            pass
        
        i = html.find("<EdTime>", j + 9) + 8
        j = html.find("</EdTime>", i)
        date_str = html[i:j].replace("-", "/")
        try:
            eddt = datetime.datetime.strptime(date_str, "%Y/%m/%d %H:%M:%S")
        except ValueError:
            pass
        
        i = html.find("<ChID>", j + 9) + 6
        j = html.find("</ChID>", i)
        ch_id = html[i:j]
        if ch_id.isdigit():
            for i, serv_info in enumerate(service):
                if serv_info[3] == ch_id:
                    serv = i
                    break
        
        i = html.find("<STSubTitle>", j + 7) + 12
        j = html.find("</STSubTitle>", i)
        subtitle = html[i:j]
        
        # HTMLエンティティの処理
        for i in range(len(CHAR9)):
            subtitle = subtitle.replace(f"&{CHAR9[i]};", CHAR10[i])
        
        return subtitle
    
    return None

def search_program(title: str, tgtdt: datetime.datetime, days: int, serv: int, service: List[List[str]], options: RenameOptions, dtflag: int) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[datetime.datetime], Optional[datetime.datetime]]:
    """番組検索"""
    if not title:
        return None, None, None, None, None
    
    # 検索開始日時設定
    stdt = tgtdt - datetime.timedelta(days=days)
    
    # しょぼいカレンダーより情報取得
    if not options.recursive_search:  # -a1 オプションでない場合
        # 日付が取得できなかった場合のメッセージ
        if days == 7:
            message = "ファイル名から日付が取得できないためファイルの"
            if dtflag == 1:
                message += "作成"
            else:
                message += "更新"
            print(f"{message}日から一週間遡って、", file=sys.stderr)
        
        # 検索開始時のメッセージ
        message = "開始" if dtflag == 1 else "終了"
        print(f"{message}日時が {tgtdt} に最も近い", file=sys.stderr)
        
        # 放送局名の表示
        if serv < 0:
            service_name = ""
        else:
            service_name = f"（{service[serv][1]}）"
        print(f"「{title}」{service_name}を検索します。\n", file=sys.stderr)
        
        # 検索開始日時を文字列に変換
        start_date = f"{stdt.year}{stdt.month:02d}{stdt.day:02d}0000"
        
        # 検索URL生成
        search_url = f"http://cal.syoboi.jp/rss2.php?start={start_date}&days={days+1}&usr=SCRename&titlefmt=%24(Title)%7C%24(ChName)%7C%24(EdTime)%7C%24(SubTitleB)"
        
        # 最大3回リトライ
        html = None
        for i in range(3):
            if i > 0:
                time.sleep(1)  # 1秒待機
            
            try:
                with urllib.request.urlopen(search_url) as response:
                    html = response.read().decode("utf-8")
                    break
            except Exception as e:
                print(f"検索エラー: {e}", file=sys.stderr)
                if i == 2:  # 最後の試行でエラー
                    print("しょぼいカレンダーにアクセスできませんでした。", file=sys.stderr)
                    return None, None, None, None, None
                continue
        
        if html:
            program_title, subtitle, serv, stdt, eddt, number = search_program_info(html, title, serv, service, tgtdt, dtflag)
            if program_title:
                return program_title, subtitle, number, stdt, eddt
        
        # 話数検索
        if options.search_episode or options.recursive_search:  # -a または -a1 オプション
            if not options.recursive_search:
                print("番組情報が見つかりませんでした。", file=sys.stderr)
            print("話数検索を行います。\n", file=sys.stderr)
            
            # search_episode_info関数を呼び出して話数検索を実行
            return search_episode_info(title, title, serv, service, options)
    
    return None, None, None, None, None

def rename_file(src_path: str, dst_path: str, options: RenameOptions) -> bool:
    """ファイルリネーム"""
    try:
        src = Path(src_path)
        dst = Path(dst_path)
        
        # リネーム先ディレクトリが存在しない場合は作成
        dst.parent.mkdir(parents=True, exist_ok=True)
        
        # リネーム実行
        if not options.test_mode:  # -t オプション
            # 強制上書きモードでない場合は存在確認
            if not options.force_rename and dst.exists():
                print(f"{dst} はすでに存在しています。", file=sys.stderr)
                return False
            
            src.rename(dst)

        print(dst)
        return True
    except Exception as e:
        print(f"リネームエラー: {e}", file=sys.stderr)
        return False

def load_replace_file(script_path: str, filename: str) -> str:
    """SCRename.rp1ファイルを読み込み、ファイル名を置換"""
    rp1_path = os.path.join(script_path, "SCRename.rp1")
    if os.path.exists(rp1_path):
        try:
            with open(rp1_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith(":"):
                        parts = line.split(",", 1)
                        if len(parts) == 2:
                            filename = filename.replace(parts[0], parts[1])
        except Exception as e:
            print(f"SCRename.rp1の読み込みでエラーが発生しました: {e}", file=sys.stderr)
    return filename

def process_episode_number(subtitle: str) -> Tuple[str, str, str, str]:
    """話数処理を行う"""
    number1 = ""
    number2 = ""
    number3 = ""
    number4 = ""

    if subtitle is None:
        return number1, number2, number3, number4

    i = 0
    # オリジナルに忠実に実装する
    while i < len(subtitle):
        if subtitle[i] == "#":
            j = i + 1
            while j < len(subtitle) and subtitle[j].isdigit():
                j += 1
            if j > i + 1:
                num = subtitle[i+1:j]
                num_int = int(num)
                num_str = str(num_int)
                number1 += num_str
                
                # 2桁の話数
                if len(num_str) < 2:
                    num_str = "0" + num_str
                number2 += num_str
                
                # 3桁の話数
                if len(num_str) < 3:
                    num_str = "0" + num_str
                number3 += num_str
                
                # 4桁の話数
                if len(num_str) < 4:
                    num_str = "0" + num_str
                number4 += num_str
            i = j
        else:
            number2 += subtitle[i]
            number3 += subtitle[i]
            number4 += subtitle[i]
            i += 1
    
    return number1, number2, number3, number4

def replace_date_time_macros(dst_path: str, dt: datetime.datetime, prefix: str = "") -> str:
    """日付・時刻のマクロを置換する"""
    # 基本の日付・時刻置換
    dst_path = dst_path.replace(f"$SC{prefix}date$", dt.strftime("%y%m%d"))
    dst_path = dst_path.replace(f"$SC{prefix}date2$", dt.strftime("%Y%m%d"))
    dst_path = dst_path.replace(f"$SC{prefix}year$", dt.strftime("%y"))
    dst_path = dst_path.replace(f"$SC{prefix}year2$", dt.strftime("%Y"))
    dst_path = dst_path.replace(f"$SC{prefix}month$", dt.strftime("%m"))
    dst_path = dst_path.replace(f"$SC{prefix}day$", dt.strftime("%d"))
    dst_path = dst_path.replace(f"$SC{prefix}quarter$", str((dt.month - 1) // 3 + 1))
    
    # 曜日の置換
    weekday_names = ["月", "火", "水", "木", "金", "土", "日"]  # 日本語
    weekday_short = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]  # 英語短縮形
    weekday_upper = [w.upper() for w in weekday_short]  # 英語大文字
    
    dst_path = dst_path.replace(f"$SC{prefix}week$", weekday_names[dt.weekday()])
    dst_path = dst_path.replace(f"$SC{prefix}week2$", weekday_short[dt.weekday()])
    dst_path = dst_path.replace(f"$SC{prefix}week3$", weekday_upper[dt.weekday()])
    
    # 時刻の置換
    dst_path = dst_path.replace(f"$SC{prefix}time$", dt.strftime("%H%M"))
    dst_path = dst_path.replace(f"$SC{prefix}time2$", dt.strftime("%H%M%S"))
    dst_path = dst_path.replace(f"$SC{prefix}hour$", dt.strftime("%H"))
    dst_path = dst_path.replace(f"$SC{prefix}minute$", dt.strftime("%M"))
    dst_path = dst_path.replace(f"$SC{prefix}second$", dt.strftime("%S"))

    # 日付調整なし
    dst_path = dst_path.replace(f"$SC{prefix}date$", dt.strftime("%y%m%d"))
    dst_path = dst_path.replace(f"$SC{prefix}date2$", dt.strftime("%Y%m%d"))
    dst_path = dst_path.replace(f"$SC{prefix}year$", dt.strftime("%y"))
    dst_path = dst_path.replace(f"$SC{prefix}year2$", dt.strftime("%Y"))
    dst_path = dst_path.replace(f"$SC{prefix}month$", dt.strftime("%m"))
    dst_path = dst_path.replace(f"$SC{prefix}day$", dt.strftime("%d"))
    dst_path = dst_path.replace(f"$SC{prefix}quarter$", str((dt.month - 1) // 3 + 1))
    dst_path = dst_path.replace(f"$SC{prefix}week$", weekday_names[dt.weekday()])
    dst_path = dst_path.replace(f"$SC{prefix}week2$", weekday_short[dt.weekday()])
    dst_path = dst_path.replace(f"$SC{prefix}week3$", weekday_upper[dt.weekday()])
    dst_path = dst_path.replace(f"$SC{prefix}time$", dt.strftime("%H%M"))
    dst_path = dst_path.replace(f"$SC{prefix}time2$", dt.strftime("%H%M%S"))
    dst_path = dst_path.replace(f"$SC{prefix}hour$", dt.strftime("%H"))

    # 日付調整後のマクロ置換
    adjusted_dt = dt
    adjusted_hour = dt.hour
    if dt.hour < 5:
        adjusted_dt = dt - datetime.timedelta(days=1)
        adjusted_hour += 24

    dst_path = dst_path.replace(f"$SC{prefix}dates$", adjusted_dt.strftime("%y%m%d"))
    dst_path = dst_path.replace(f"$SC{prefix}date2s$", adjusted_dt.strftime("%Y%m%d"))
    dst_path = dst_path.replace(f"$SC{prefix}years$", adjusted_dt.strftime("%y"))
    dst_path = dst_path.replace(f"$SC{prefix}year2s$", adjusted_dt.strftime("%Y"))
    dst_path = dst_path.replace(f"$SC{prefix}months$", adjusted_dt.strftime("%m"))
    dst_path = dst_path.replace(f"$SC{prefix}days$", adjusted_dt.strftime("%d"))
    dst_path = dst_path.replace(f"$SC{prefix}quarters$", str((adjusted_dt.month - 1) // 3 + 1))
    dst_path = dst_path.replace(f"$SC{prefix}weeks$", weekday_names[adjusted_dt.weekday()])
    dst_path = dst_path.replace(f"$SC{prefix}week2s$", weekday_short[adjusted_dt.weekday()])
    dst_path = dst_path.replace(f"$SC{prefix}week3s$", weekday_upper[adjusted_dt.weekday()])
    dst_path = dst_path.replace(f"$SC{prefix}times$",  f"{adjusted_hour:02d}" + adjusted_dt.strftime("%M"))
    dst_path = dst_path.replace(f"$SC{prefix}time2s$", f"{adjusted_hour:02d}" + adjusted_dt.strftime("%M%S"))
    dst_path = dst_path.replace(f"$SC{prefix}hours$",  f"{adjusted_hour:02d}")

    return dst_path

def replace_program_info_macros(dst_path: str, main_title: str, subtitle: str, service_name: str) -> str:
    """番組情報のマクロを置換する"""
    dst_path = dst_path.replace("$SCservice$", service_name)
    dst_path = dst_path.replace("$SCpart$", "")
    dst_path = dst_path.replace("$SCtitle$", main_title)
    dst_path = dst_path.replace("$SCtitle2$", main_title.replace(" ", "").upper())
    dst_path = dst_path.replace("$SCsubtitle$", subtitle if subtitle else "")
    return dst_path

def apply_rp2_replacements(dst_path: str, script_path: str) -> str:
    """SCRename.rp2の置換ルールを適用する"""
    rp2_path = os.path.join(script_path, "SCRename.rp2")
    if os.path.exists(rp2_path):
        try:
            with open(rp2_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith(":"):
                        parts = line.split(",", 1)
                        if len(parts) == 2:
                            dst_path = dst_path.replace(parts[0], parts[1])
        except Exception as e:
            print(f"SCRename.rp2の読み込みでエラーが発生しました: {e}", file=sys.stderr)
    return dst_path

def replace_invalid_chars(dst_path: str, rename_format: str) -> str:
    """使用不可文字を置換する"""
    prefix = ""
    if len(rename_format) >= 2 and rename_format[1] == ":" and len(dst_path) >= 2 and dst_path[1] == ":":
        prefix = dst_path[:2]
        dst_path = dst_path[2:]

    for i in range(len(CHAR6)):
        dst_path = dst_path.replace(CHAR6[i], CHAR7[i])
    return prefix + dst_path

def remove_unnecessary_spaces(dst_path: str) -> str:
    """不要な空白を削除する"""
    # バックスラッシュ前の空白を削除
    i = 2
    while True:
        i = dst_path.find("\\", i)
        if i < 0:
            break
        j = i - 1
        while j >= 0 and dst_path[j] == " ":
            j -= 1
        if j < i - 1:
            dst_path = dst_path[:j+1] + dst_path[i:]
        i += 1

    # 連続する空白を1つに
    dst_path = dst_path.strip()
    i = 0
    while i < len(dst_path):
        if dst_path[i] in [" ", "　"]:
            j = i + 1
            while j < len(dst_path) and dst_path[j] in [" ", "　"]:
                j += 1
            if dst_path[i-1] in [":", "\\"]:
                i -= 1
            dst_path = dst_path[:i+1] + dst_path[j:]
        i += 1
    
    return dst_path

def generate_full_path(dst_path: str, file_path: str, rpath: str) -> str:
    """フルパスを生成する"""
    # UNCパスの場合
    if dst_path.startswith("\\\\"):
        return dst_path
    
    # ドライブレター付きのパスの場合
    if len(dst_path) >= 2 and dst_path[1] == ":":
        return dst_path
    
    # 相対パスの場合
    if dst_path.startswith(os.sep):
        # ドライブレターがある場合は追加
        if len(file_path) >= 2 and file_path[1] == ":":
            return os.path.join(file_path[:2], dst_path)
        return dst_path
    
    # その他の場合（相対パス）
    # パスの末尾にセパレータがない場合は追加
    if not rpath.endswith(os.sep):
        rpath = os.path.join(rpath, "")
    return os.path.join(rpath, dst_path)

def process_file(file_path: str, rename_format: str, options: RenameOptions, service: List[List[str]]) -> bool:
    """ファイル処理"""
    # ファイルパス、ファイル名、拡張子、タイトル開始位置取得
    rpath, filename, ext = get_file_info(file_path)
    print(f"Path: {rpath}, Filename: {filename}, Ext: {ext}", file=sys.stderr)
    
    # 日付取得（タイトル開始位置も同時に取得）
    tgtdt, dtflag, days, title_pos = get_date_from_title(filename, options.start_pos)
    print(f"Date: {tgtdt}, Flag: {dtflag}, Days: {days}, Title Position: {title_pos}", file=sys.stderr)
    
    # コマンドライン引数で指定された位置を優先
    if options.start_pos > 0:
        title_pos = options.start_pos

    raw_title = filename
    if title_pos > 1:
        raw_title = filename[title_pos:]

    # SCRename.rp1ファイルの読み込みとファイル名置換
    script_path = os.path.dirname(sys.argv[0])
    raw_title = load_replace_file(script_path, raw_title)
    print(f"After RP1: {raw_title}", file=sys.stderr)

    # ファイル名先頭部分削除
    raw_title = remove_leading_chars(raw_title)
    print(f"Raw Title: {raw_title}", file=sys.stderr)

    # 全角半角ローマ数字記号変換
    normalized_title = convert_chars(raw_title)
    print(f"Normalized Title: {normalized_title}", file=sys.stderr)

    # タイトル取得
    main_title = get_title(normalized_title, options.search_len)
    print(f"Main Title: {main_title}", file=sys.stderr)

    # 放送局名取得
    serv = get_service(normalized_title, main_title, service, options.start_pos)
    if serv >= 0:
        print(f"Service: {service[serv][0]} ({service[serv][1]})", file=sys.stderr)
    else:
        print("Service: Unknown", file=sys.stderr)

    # 番組検索
    program_info = None
    subtitle = None
    number = None
    stdt = None
    eddt = None

    # -a1オプションが指定されていない場合は通常の番組情報検索を実行
    if not options.recursive_search:
        program_info, subtitle, number, stdt, eddt = search_program(main_title, tgtdt, days, serv, service, options, dtflag)

    # 通常の検索で見つからない場合、または-a1オプションが指定されている場合は話数検索を実行
    if not program_info and (options.search_episode or options.recursive_search):
        print("話数検索を行います。\n", file=sys.stderr)
        program_info, subtitle, number, stdt, eddt = search_episode_info(normalized_title, main_title, serv, service, options)

    if not program_info:
        if not options.force_rename:
            print(f"{main_title} の番組情報が見つかりませんでした。", file=sys.stderr)
            return False
        else:
            print("強制リネームを行います。\n", file=sys.stderr)
            # 強制リネーム時の処理
            sep_pos = normalized_title.find(SEP, 1)
            if sep_pos > 1:
                main_title = normalized_title[:sep_pos]
            else:
                main_title = normalized_title
            # 強制リネーム時は開始時刻から30分後を終了時刻とする
            stdt = tgtdt
            eddt = stdt + datetime.timedelta(minutes=30)
    else:
        # サブタイトル必須の処理
        if options.require_subtitle and not subtitle:
            print(f"{program_info} のサブタイトルを取得できなかったため処理を中止しました。", file=sys.stderr)
            return False
        # 番組情報から取得した時刻を使用
        if not stdt:
            stdt = tgtdt
        if not eddt:
            eddt = stdt + datetime.timedelta(minutes=30)  # デフォルト値
        # 番組情報から取得したタイトルを使用
        main_title = program_info

    # リネーム書式設定
    dst_path = rename_format
    
    # 話数処理
    number1, number2, number3, number4 = process_episode_number(number)
    dst_path = dst_path.replace("$SCnumber1$", number1)
    dst_path = dst_path.replace("$SCnumber$", number2)
    dst_path = dst_path.replace("$SCnumber2$", number2)
    dst_path = dst_path.replace("$SCnumber3$", number3)
    dst_path = dst_path.replace("$SCnumber4$", number4)

    # 開始時刻の置換
    dst_path = replace_date_time_macros(dst_path, stdt, "")

    # 終了時刻の置換
    dst_path = replace_date_time_macros(dst_path, eddt, "ed")

    # 放送局名の置換
    service_name = service[serv][2] if serv >= 0 else ""
    dst_path = replace_program_info_macros(dst_path, main_title, subtitle, service_name)

    # SCRename.rp2 読み込み＆リネーム名置換
    dst_path = apply_rp2_replacements(dst_path, script_path)

    # 使用不可文字置換
    dst_path = replace_invalid_chars(dst_path, rename_format)

    # 不要空白削除
    if not options.keep_spaces:
        dst_path = remove_unnecessary_spaces(dst_path)

    # フルパス生成
    dst_path = generate_full_path(dst_path, file_path, rpath)

    # 256文字以上ファイルパス削除
    max_len = 255 - len(ext)
    if len(dst_path) > max_len:
        print("ファイルパスが256文字以上のため切り詰めます。", file=sys.stderr)
        dst_path = dst_path[:max_len]
    
    # リネーム実行
    return rename_file(file_path, dst_path + ext, options)

def load_service_file(script_path: str) -> List[List[str]]:
    """SCRename.srvファイルを読み込み、サービス情報を返す"""
    service = []
    srv_path = os.path.join(script_path, "SCRename.srv")
    try:
        with open(srv_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith(":"):
                    parts = line.split(",")
                    if len(parts) >= 4 and parts[0]:
                        service.append(parts[:4])
    except FileNotFoundError:
        print(f"{srv_path} がありません。", file=sys.stderr)
        time.sleep(1)
        sys.exit(1)
    return service

def search_episode_info(normalized_title: str, main_title: str, serv: int, service: List[List[str]], options: RenameOptions) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[datetime.datetime], Optional[datetime.datetime]]:
    """話数検索を行う"""
    # 話数検索
    episode_number = None
    title = main_title
    title2 = main_title.replace(" ", "").upper()
    tid = None
    tid_title = None

    # ファイル名から話数を取得
    for i in range(2, len(normalized_title) - 2):
        char = normalized_title[i]
        if char in "「『":
            break
        elif char in " " + SEP:
            next_char = normalized_title[i + 1]
            if next_char == NIND or next_char == "第":
                j = i + 2
                while j < len(normalized_title) and normalized_title[j].isdigit():
                    j += 1
                if j > i + 2:
                    if (next_char == NIND and normalized_title[j] in " " + SEP) or (next_char == "第" and normalized_title[j] == "話"):
                        episode_number = int(normalized_title[i + 2:j])
                        break

    if episode_number is None:
        print("ファイル名から話数を取得できませんでした。\n", file=sys.stderr)
        return None, None, None, None, None

    # タイトル部分を取得
    for j in range(2, i):
        if normalized_title[j] in SEP + CHAR4 + CHAR5 + "～":
            break
    title = normalized_title[:j].rstrip()
    title2 = title.replace(" ", "").upper()

    # SCRename.tidファイルからTIDを取得
    tid, tid_title = get_tid_from_cache(title, title2)

    # しょぼいカレンダーからTIDを取得
    if tid is None:
        # タイトルをURLエンコード
        encoded_title = urllib.parse.quote(title.encode("utf-8"))

        # しょぼいカレンダーにアクセス
        for i in range(3):
            if i > 0:
                time.sleep(1)
            try:
                with urllib.request.urlopen(f"http://cal.syoboi.jp/find?kw={encoded_title}") as response:
                    content = response.read().decode("utf-8")
                    break
            except Exception as e:
                if i == 2:  # 最後の試行でエラー
                    print("しょぼいカレンダーにアクセスできませんでした。", file=sys.stderr)
                    return None, None, None, None, None
                continue

        # TIDを取得
        i = len(content)
        while True:
            i = content.rfind("/tid/", 0, i)
            if i < 0:
                break
            j = i + 5
            while j < len(content) and content[j].isdigit():
                j += 1
            if j > i + 5:
                tid = int(content[i + 5:j])
                j += 2
                k = content.find("</a>", j)
                if k > j:
                    tid_title = content[j:k]
                    tid_title = tid_title.replace("?", "？").replace("!", "！")
                    if tid_title.replace(" ", "").upper().startswith(title2):
                        print("しょぼいカレンダーから", end="", file=sys.stderr)
                        break
            i -= 1

        if i < 0:
            print(f"「{title}」の TID を取得できませんでした。\n", file=sys.stderr)
            return None, None, None, None, None

        # TIDキャッシュを更新
        update_tid_cache(tid, tid_title)

    # 話数情報を取得
    service_param = ""
    if serv >= 0 and service[serv][3]:
        service_param = f"&ChID={service[serv][3]}"
        print(f"「{tid_title}」の TID（{tid}）を取得しました。", file=sys.stderr)
        print(f"第{episode_number}話（{service[serv][1]}）の情報を検索します。\n", file=sys.stderr)
    else:
        print(f"「{tid_title}」の TID（{tid}）を取得しました。", file=sys.stderr)
        print(f"第{episode_number}話の情報を検索します。\n", file=sys.stderr)

    # しょぼいカレンダーから話数情報を取得
    for i in range(3):
        if i > 0:
            time.sleep(1)
        try:
            with urllib.request.urlopen(f"http://cal.syoboi.jp/db.php?Command=ProgLookup&TID={tid}{service_param}&Count={episode_number}&Fields=StTime,EdTime,ChID,STSubTitle&JOIN=SubTitles") as response:
                content = response.read().decode("utf-8")
                break
        except Exception as e:
            if i == 2:  # 最後の試行でエラー
                print("しょぼいカレンダーにアクセスできませんでした。", file=sys.stderr)
                return None, None, None, None, None
            continue

    # 話数情報を解析
    i = content.find("<StTime>")
    if i > 0:
        i += 8
        j = content.find("</StTime>", i)
        start_time = content[i:j].replace("-", "/")
        if start_time:
            stdt = datetime.datetime.strptime(start_time, "%Y/%m/%d %H:%M:%S")

        i = content.find("<EdTime>", j + 9) + 8
        j = content.find("</EdTime>", i)
        end_time = content[i:j].replace("-", "/")
        if end_time:
            eddt = datetime.datetime.strptime(end_time, "%Y/%m/%d %H:%M:%S")

        i = content.find("<ChID>", j + 9) + 6
        j = content.find("</ChID>", i)
        ch_id = content[i:j]
        if ch_id.isdigit():
            for i in range(len(service)):
                if service[i][3] == ch_id:
                    serv = i
                    break

        i = content.find("<STSubTitle>", j + 7) + 12
        j = content.find("</STSubTitle>", i)
        subtitle = content[i:j]

        # HTMLエンティティを変換
        for i in range(len(CHAR9)):
            subtitle = subtitle.replace(f"&{CHAR9[i]};", CHAR10[i])

        return tid_title, subtitle, f"#{episode_number}", stdt, eddt

    return None, None, None, None, None

def main():
    # 変数初期化
    options = RenameOptions()
    argv = []
    argc = 0
    elen = 0
    days = 1
    pos = 0
    serv = -1
    dtflag = 0
    tgtdt = None
    stdt = None
    eddt = None
    
    # 引数処理
    for arg in sys.argv[1:]:
        if arg.lower() in ["-h", "-?"]:
            print("\nSCRename.py [オプション] \"ファイル\" \"リネーム書式\"")
            print("              [タイトル開始位置] [検索文字数]\n")
            sys.exit(1)
        elif arg.lower() == "-t":
            options.test_mode = True
        elif arg.lower() == "-n":
            options.require_subtitle = True
        elif arg.lower() == "-f":
            options.force_rename = True
        elif arg.lower() == "-s":
            options.keep_spaces = True
        elif arg.lower() == "-a":
            options.search_episode = True
        elif arg.lower() == "-a1":
            options.recursive_search = True
        else:
            argv.append(arg)
            argc += 1

    # 起動時処理
    print("\nSCRename 動作中...\n", file=sys.stderr)
    if argc < 2:
        print(argv[0] if argv else "")
        print("パラメータが足りません。", file=sys.stderr)
        time.sleep(1)
        sys.exit(1)
    elif not argv[0]:
        print("処理対象のファイルが指定されていません。", file=sys.stderr)
        time.sleep(1)
        sys.exit(1)
    elif not argv[1]:
        print(argv[0])
        print("リネーム書式が指定されていません。", file=sys.stderr)
        time.sleep(1)
        sys.exit(1)

    # 実体名最大文字数取得
    elen = max(len(x) for x in CHAR9) + 2

    # スクリプトのパスを取得
    script_path = os.path.dirname(sys.argv[0])

    # SCRename.exc 読み込み
    exc_path = os.path.join(script_path, "SCRename.exc")
    if os.path.exists(exc_path):
        with open(exc_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith(":"):
                    if line.upper() in argv[0].upper():
                        print(argv[0])
                        print("対象外のファイルのため処理しませんでした。", file=sys.stderr)
                        sys.exit(1)

    # リネーム元ファイル存在確認
    if not options.test_mode:
        if not os.path.exists(argv[0]):
            print(f"{argv[0]} がありません。", file=sys.stderr)
            time.sleep(1)
            sys.exit(1)

    # SCRename.srv 読み込み
    service = load_service_file(script_path)

    # 検索文字数の取得
    if argc > 3 and argv[3].isdigit():
        options.search_len = int(argv[3])

    # タイトル開始位置の取得
    if argc > 2 and argv[2].isdigit():
        options.start_pos = int(argv[2])

    if not process_file(argv[0], argv[1], options, service):
        if not options.force_rename:
            sys.exit(1)

if __name__ == "__main__":
    main() 