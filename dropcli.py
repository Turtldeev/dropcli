import asyncio
import os
import sys
import typing as t

import httpx
from bs4 import BeautifulSoup


API_URL_TEMPLATE = "https://dropmail.me/api/graphql/{token}"


class DropmailError(Exception):
    pass


def get_api_url() -> str:
    token = os.getenv("DROPMAIL_TOKEN")
    if not token:
        # Минимально 8 символов. Генерируем безопасную строку по умолчанию
        token = os.urandom(16).hex()
    if len(token) < 8:
        raise DropmailError("DROPMAIL_TOKEN должен быть длиной не менее 8 символов")
    return API_URL_TEMPLATE.format(token=token)


async def graphql_request(client: httpx.AsyncClient, query: str, variables: t.Optional[dict] = None) -> dict:
    payload: dict[str, t.Any] = {"query": query}
    if variables:
        payload["variables"] = variables

    response = await client.post("/", json=payload)
    response.raise_for_status()
    data = response.json()

    if "errors" in data and data["errors"]:
        # Пробрасываем первую ошибку для краткости
        message = data["errors"][0].get("message", "GraphQL error")
        raise DropmailError(message)

    return data["data"]


async def create_session(client: httpx.AsyncClient) -> tuple[str, str]:
    # Пытаемся запросить адрес сразу в introduceSession
    query = (
        "mutation($withAddress: Boolean!) { "
        "  introduceSession(input: { withAddress: $withAddress }) { "
        "    id "
        "    addresses { address } "
        "  } "
        "}"
    )

    data = await graphql_request(client, query, {"withAddress": True})
    session = data.get("introduceSession")
    if not session:
        raise DropmailError("Не удалось создать сессию Dropmail")

    session_id: str = session["id"]
    addresses: list[dict] = session.get("addresses", [])
    if not addresses:
        # На некоторых версиях схемы адрес не возвращается сразу — пробуем запросить отдельно
        temp_email = await get_first_address(client, session_id)
    else:
        temp_email = addresses[0]["address"]

    return session_id, temp_email


async def get_first_address(client: httpx.AsyncClient, session_id: str) -> str:
    query = (
        "query($id: ID!) { "
        "  session(id: $id) { addresses { address } } "
        "}"
    )
    data = await graphql_request(client, query, {"id": session_id})
    session = data.get("session") or {}
    addresses: list[dict] = session.get("addresses", [])
    if not addresses:
        raise DropmailError("Сессия создана, но адрес не получен")
    return addresses[0]["address"]


async def fetch_mails(client: httpx.AsyncClient, session_id: str) -> list[dict]:
    # Запрашиваем компактный набор полей, совместимый с публичными примерами
    query = (
        "query($id: ID!) { "
        "  session(id: $id) { "
        "    mails { "
        "      id "
        "      fromAddr "
        "      toAddr "
        "      headerSubject "
        "      text "
        "      html "
        "      downloadUrl "
        "    } "
        "  } "
        "}"
    )
    data = await graphql_request(client, query, {"id": session_id})
    session = data.get("session") or {}
    return session.get("mails", [])


def extract_plain_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # Добавим переносы для <br> и <p>, чтобы текст был читабельным
    for br in soup.find_all(["br", "p", "div"]):
        br.append("\n")
    text = soup.get_text()
    # Нормализуем множественные пустые строки
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join([line for line in lines if line])


async def run_loop(poll_interval_sec: float = 5.0) -> None:
    api_url = get_api_url()
    async with httpx.AsyncClient(base_url=api_url, timeout=httpx.Timeout(30.0)) as client:
        session_id, temp_email = await create_session(client)

        print("\n" + "=" * 35)
        print(f"  Temporary email: {temp_email}")
        print("=" * 35 + "\n")

        print("Ожидание новых писем. Нажмите Ctrl+C для выхода.")
        processed_mail_ids: set[str] = set()

        while True:
            try:
                mails = await fetch_mails(client, session_id)
            except DropmailError as exc:
                print(f"\n[Ошибка] Не удалось получить почту: {exc}")
                await asyncio.sleep(poll_interval_sec)
                continue

            new_count = 0
            for mail in mails:
                mail_id = mail.get("id") or f"{mail.get('fromAddr')}:{mail.get('headerSubject')}"
                if mail_id in processed_mail_ids:
                    continue

                sender = (mail.get("fromAddr") or "").strip()
                subject = (mail.get("headerSubject") or "").strip()
                text_body = (mail.get("text") or "").strip()
                html_body = mail.get("html")

                print("\n--- Новое письмо! ---")
                print(f"От: {sender}")
                print(f"Тема: {subject}")
                print("-" * 20)

                if html_body:
                    try:
                        parsed_text = extract_plain_text_from_html(html_body)
                        if parsed_text:
                            print(parsed_text)
                        else:
                            print(text_body or "(пустое тело)")
                    except Exception:
                        print(text_body or "(пустое тело)")
                else:
                    print(text_body or "(пустое тело)")

                download_url = mail.get("downloadUrl")
                if download_url:
                    print("-" * 20)
                    print(f"Скачать оригинал: {download_url}")

                print("=" * 30)
                processed_mail_ids.add(mail_id)
                new_count += 1

            if new_count == 0:
                # Визуальный индикатор ожидания
                print(".", end="", flush=True)

            await asyncio.sleep(poll_interval_sec)


async def main() -> None:
    try:
        await run_loop()
    except KeyboardInterrupt:
        print("\nЗавершение работы по запросу пользователя.")
    except httpx.HTTPError as exc:
        print(f"HTTP ошибка: {exc}")
        sys.exit(1)
    except DropmailError as exc:
        print(f"Ошибка Dropmail: {exc}")
        sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())


