import os
import smtplib
import ssl
import time

from csv import DictReader
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Generator, List

comelec_username = os.getenv("COMELEC_USERNAME")


@dataclass
class Candidate:
    name: str
    email_addr: str
    positions: List[str]

    @property
    def nominations(self) -> int:
        return len(self.positions)

    def __eq__(self, other: "Candidate") -> bool:
        if not isinstance(other, Candidate):
            return False
        return hash(other.email_addr) == hash(self.email_addr)

    def __hash__(self) -> int:
        return hash(self.email_addr)

    def __add__(self, other: "Candidate") -> "Candidate":
        if not isinstance(other, Candidate):
            raise TypeError(f"Addition not supported between {type(self).__name__} and {type(other).__name__}.")
        if self != other:
            raise ValueError(f"Can only combine two Candidates with the same email and name.")
        new_positions = list(set(self.positions + other.positions))
        return Candidate(name=self.name, email_addr=self.email_addr, positions=new_positions)


class Message:
    def __init__(self, candidate: Candidate) -> None:
        self.candidate = candidate
        self.response_url = "https://bit.ly/2026candidates2223"


class TextMessage(Message):
    def __init__(self, candidate: Candidate) -> None:
        super().__init__(candidate=candidate)
        self.body = (
            f"Congratulations {candidate.name}! You've been nominated "
            f"for the following positions {candidate.positions} for A.Y. 2022 - 2023.\n\n"
            f"If you wish to pursue candidacy please click the following link:\n"
            f"{self.response_url}"
        )

    def mime_text(self) -> MIMEText:
        return MIMEText(self.body, "plain")


class HTMLMessage(Message):
    def __init__(self, candidate: Candidate) -> None:
        super().__init__(candidate=candidate)
        with open("templates/nomination.html", "r") as f:
            self.body = f.read().format(**{
                "nominee": candidate.name,
                "positions": self.format_positions(),
                "response_url": self.response_url,
            })

    def format_positions(self) -> str:
        font_size = "15px"
        if self.candidate.nominations < 2:
            font_size = "18px"
        return "\n".join([f"<li style=\"font-size: {font_size};\">{pos}</li>" for pos in self.candidate.positions])

    def mime_text(self) -> MIMEText:
        return MIMEText(self.body, "html")


class Email:
    def __init__(self, candidate: Candidate) -> None:
        self.candidate = candidate
        self.message = MIMEMultipart("alternative")
        self.message["Subject"] = self.format_subject()
        self.message["From"] = os.getenv("COMELEC_USERNAME")
        self.message["To"] = candidate.email_addr

    def format_subject(self) -> str:
        subject = "Nomination for LU4"
        if self.candidate.nominations > 1:
            return f"{subject} Multiple Positions"
        return f"{subject} {self.candidate.positions[0]}"
    
    def attach(self, payload: MIMEText) -> None:
        self.message.attach(payload=payload)

    def get_message(self) -> MIMEMultipart:
        return self.message


class CandidatePool:
    def __init__(self, fname: str) -> None:
        self.pool = {}
        with open(fname, "r") as f:
            for row in DictReader(f):
                self.build_candidate(row=row)
                
    def build_candidate(self, row: dict) -> None:
        if not all(row.values()):
            return None

        row["positions"] = [row["positions"]]
        candidate = Candidate(**row)
        if candidate.email_addr in self.pool:
            self.pool[candidate.email_addr] += candidate
        else:
            self.pool[candidate.email_addr] = candidate

    @property
    def candidates(self) -> Generator:
        yield from self.pool.values()

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.pool})"


def get_recipients() -> Generator:
    yield from CandidatePool(fname="nominees.csv").candidates


def build_message(candidate: Candidate) -> MIMEMultipart:
    email = Email(candidate=candidate)
    text = TextMessage(candidate=candidate)
    html = HTMLMessage(candidate=candidate)
    email.attach(payload=text.mime_text())
    email.attach(payload=html.mime_text())
    return email.get_message()


def main():
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", port=465, context=context) as server:
        server.login(user=comelec_username, password=os.getenv("APP_PASSWORD"))
        for recipient in get_recipients():
            print(recipient)
            message = build_message(candidate=recipient)
            server.sendmail(from_addr=comelec_username, to_addrs=recipient.email_addr, msg=message.as_string())
            time.sleep(5)


if __name__ == "__main__":
    main()