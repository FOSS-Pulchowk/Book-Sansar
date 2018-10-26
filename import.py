import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine('postgres://evzazpuapjscve:ae1e41a4f5302a52848eef021e3cca397ca9cbab9665958874ecc5154261f8b7@ec2-184-73-169-151.compute-1.amazonaws.com:5432/d4v8ok9mo8ptre')
db = scoped_session(sessionmaker(bind=engine))


def main():
    f = open("books.csv", "r")  # needs to be opened during reading csv
    reader = csv.reader(f)
    next(reader)
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
               {"isbn": isbn, "title": title, "author": author, "year": year})
        db.commit()
        print(f"Added book with ISBN: {isbn} Title: {title}  Author: {author}  Year: {year}")


if __name__ == '__main__':
    main()