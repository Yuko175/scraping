import numpy as np
import requests
from requests.exceptions import Timeout
from bs4 import BeautifulSoup
import io
import re
import time


# 基本情報
class Data:
    base_url = "URL"
    keyword = "キーワード"
    selectors = ["題名", "本文"]
    depth = 0
    MAX_RETRY = 3

    # 複数ページ対応
    base_urls = [base_url]
    page_num = 2
    while True:
        url = f"{base_url}page/{page_num}/"
        response = requests.get(url)
        if response.status_code == 200:
            page_num += 1
            base_urls.append(url)
            print(url)
        else:
            break


# 関数の実行
def main():
    base_urls = Data.base_urls
    urls = get_internal_urls(base_urls, Data.depth, Data.keyword)
    text = get_text_from_urls(urls, Data.selectors)
    save_text_to_file(text)

    # 抽出したURL一覧をターミナルにプリント
    for i in range(len(urls)):
        print(urls[i])


# URLの検索
def get_internal_urls(base_urls, depth, keyword):
    urls = []
    pre_extracted_urls = base_urls

    # サイトの深さ
    for current_depth in range(depth + 1):
        print(f"Start depth: {current_depth}.........................")
        extracted_urls = []

        # 抽出
        for i, pre_url in enumerate(pre_extracted_urls):
            retry_count = 0
            while retry_count < Data.MAX_RETRY:  # リトライは "MAX_RETRY" 回まで
                try:
                    res = requests.get(pre_url, timeout=10.0)
                    break  # 成功したらループを抜ける
                except (Timeout, ConnectionError, requests.exceptions.HTTPError) as e:
                    retry_count += 1
                    time.sleep(1)
                    if retry_count == Data.MAX_RETRY:
                        print(str(i + 1) + " / " + str(len(urls)) + f" Error: {str(e)}")
                        # エラーが発生した場合は飛ばして次に進む
                        break

            # キーワードが入っているもののみ抽出
            soup = BeautifulSoup(res.text, "html.parser")
            if keyword:
                elems = soup.find_all(href=re.compile(keyword))
            else:
                elems = soup.find_all("a")  # キーワードが指定されていない場合はすべてのリンクを取得
            print(f"{len(elems)} URLs extracted ({i + 1}/{len(pre_extracted_urls)})")

            # URL生成
            for elem in elems:
                if "href" in elem.attrs:
                    url = elem.attrs["href"]
                    if not url.startswith("http"):
                        url = pre_url + url
                    extracted_urls.append(url)

        # 重複の削除
        pre_extracted_urls = np.unique(extracted_urls).tolist()
        urls.extend(pre_extracted_urls)
        urls = np.unique(urls).tolist()
        print(f"Total: {len(urls)} URLs")

    print("Start extracting html....")
    return urls


# テキストの抽出
def get_text_from_urls(urls, selectors):
    texts = []

    for i in range(len(urls)):
        if i != 0:
            texts.append("")
        retry_count = 0

        # 抽出
        while retry_count < Data.MAX_RETRY:
            try:
                res = requests.get(urls[i], timeout=10.0)
                res.raise_for_status()  # レスポンスのステータスコードをチェック
                soup = BeautifulSoup(res.text, "html.parser")
                text = ""
                for selector in selectors:
                    elems = soup.select(selector)
                    for elem in elems:
                        text += str(elem.get_text()) + "\n"
                texts.append(text)
                print(str(i + 1) + " / " + str(len(urls)) + " finished")  # 終了報告
                break  # 成功したらループを抜ける
            except (Timeout, ConnectionError, requests.exceptions.HTTPError) as e:
                retry_count += 1
                time.sleep(1)
                if retry_count == Data.MAX_RETRY:
                    print(str(i + 1) + " / " + str(len(urls)) + f" Error: {str(e)}")
                    # エラーが発生した場合は飛ばして次に進む
                    break

    return "\n\n".join(texts)


# txtファイルにする
def save_text_to_file(text):
    with io.open("text.txt", "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    main()
