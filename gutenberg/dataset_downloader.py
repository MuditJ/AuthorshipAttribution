from random import sample
import sqlite3
import requests
from bs4 import BeautifulSoup


class ArticlesDownloader:
    def __init__(self):
        self.top_100_authors_url = "http://www.gutenberg.org/browse/scores/top"
        self.base_gutenberg_url = "http://www.gutenberg.org"
        self.periods = [".", "!", "?"]
        self.db_uri = "gutenberg.sqlite3"

        self.initiate_db()

    def get_db(self):
        con = sqlite3.connect(self.db_uri)
        cur = con.cursor()
        return cur, con

    def initiate_db(self):
        cur, con = self.get_db()
        try:
            cur.execute("select * from articles")
        except Exception:
            cur.execute(
                """
                create table articles (
                    id integer primary key,
                    auth_name varchar(100),
                    article text
                )
                """
            )
            con.commit()
        con.close()

    def get_top_100_authors_element(self):
        res = requests.get(self.top_100_authors_url)
        soup = BeautifulSoup(res.text, "html.parser")
        ele = soup.select(".body > ol:nth-child(21)")[0]
        authors = ele.find_all(name="li")
        authors_list = []
        for author in authors:
            author = author.find(name="a")
            d = {
                "link": self.base_gutenberg_url + author["href"],
                "name": author.text.split("(")[0].strip(),
            }
            authors_list.append(d)
        return authors_list

    def get_author_details(self, author_link):
        res = requests.get(author_link)
        soup = BeautifulSoup(res.text, "html.parser")
        auth_id = author_link.split("#")[-1]
        ele = soup.find(name="a", attrs={"name": auth_id})
        ul = ele.find_next("ul")
        items = ul.find_all(name="li", attrs={"class": "pgdbetext"})
        book_names = set()
        for item in items:
            # link = item.find(name="a")
            if item.text.split("(")[-1].strip() != "as Author)":
                continue
            if item.text.split("(")[-2].strip() != "English)":
                continue
            if "Project Gutenberg" in item.text:
                continue
            item = item.find(name="a")
            if item.text.strip() in book_names:
                continue
            book_names.add(item.text.strip())
            d = {
                "link": self.base_gutenberg_url + item["href"],
                "name": item.text.strip(),
            }
            yield d

    def get_book_content(self, book_link):
        book_id = book_link.split("/")[-1]
        book_html_url = self.base_gutenberg_url + \
            "/files/%s/%s-h/%s-h.htm" % (book_id, book_id, book_id)
        res = requests.get(book_html_url)
        content = res.text
        soup = BeautifulSoup(content, "html.parser")
        chapters = soup.find_all(name="h2")
        filtered_chapters = []
        for chapter in chapters:
            if "chapter" not in chapter.text.lower():
                continue
            filtered_chapters.append(chapter)
        articles = []
        for chapter in filtered_chapters:
            article = ""
            for tag in chapter.next_siblings:
                if tag.name == "h2":
                    break
                if tag.name != "p":
                    continue
                article += tag.text
                if len(article.split()) > 1000:
                    if article.strip()[-1] in self.periods or \
                            article.strip()[-2] in self.periods:
                        break
            articles.append(article)
        return articles

    def run(self):
        print("* Getting list of authors..")
        authors_list = self.get_top_100_authors_element()
        n_authors = 0
        cur, con = self.get_db()
        for author in authors_list:
            all_articles = set()
            print("** Obtaining books of author:", author["name"])
            books = self.get_author_details(author["link"])
            for book in books:
                print("*** Getting articles from book:", book["name"])
                articles = self.get_book_content(book["link"])
                for article in articles:
                    all_articles.add(article)
                if len(all_articles) > 200:
                    break
            if len(all_articles) < 50:
                print("Author has less than 50 articles")
                continue
            chosen_articles = sample(all_articles, 50)
            print("** Added 50 articles")
            for article in chosen_articles:
                cur.execute(
                    """
                    insert into articles (auth_name, article) values
                    (?, ?)
                    """, (author["name"], article)
                )
            con.commit()
            n_authors += 1
            if n_authors >= 50:
                break
        con.close()

    def demo(self):
        al = self.get_top_100_authors_element()
        al = al[0]
        ul = self.get_author_details(al["link"])
        for e in ul:
            ee = e
            break
        content = self.get_book_content(ee["link"])
        print(content[0])


if __name__ == '__main__':
    dl = ArticlesDownloader()
    dl.run()
