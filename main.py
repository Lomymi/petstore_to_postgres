import os
from dotenv import load_dotenv
import requests
import psycopg

load_dotenv()


def get_available_pets(count_pets):
    available_pets = []
    params = {
        "status": "available"
    }

    url = "https://petstore.swagger.io/v2/pet/findByStatus"
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()
    for pet in data[:count_pets]:
        pet_id = pet.get("id")

        if pet_id is None:
            raise ValueError("У питомца из API отсутствует id")
        if type(pet_id) is not int:
            raise ValueError("ID питомца должен быть целым числом")
        if not (-9223372036854775808 <= pet_id <= 9223372036854775807):
            raise ValueError("ID питомца выходит за диапазон BIGINT")

        available_pets.append({"id": pet_id,
                               "name": pet.get("name"),
                               "status": pet.get("status")})
    return available_pets


def save_pets(available_pets):
    with psycopg.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    ) as connection:
        with connection.cursor() as cursor:
            for pet in available_pets:
                cursor.execute(
                    """INSERT INTO pets (id, name, status) 
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO UPDATE
                    SET name = EXCLUDED.name,
                    status = EXCLUDED.status;""",
                    (pet["id"], pet["name"], pet["status"])
                )
    return len(available_pets)


def ask_pet_count():
    while True:
        try:
            count_pets = int(input(
                "Введите кол-во питомцев, которых хотите записать: "
            ).strip())

            if count_pets <= 0:
                raise ValueError("Количество питомцев должно быть больше нуля\n")

            return count_pets
        except ValueError as error:
            print(f"Ошибка ввода: {error}")


try:
    count_pets = ask_pet_count()
    available_pets = get_available_pets(count_pets)
    saved_count = save_pets(available_pets)
    print(f"Обработано питомцев: {saved_count}")
except requests.HTTPError as error:
    print(f"HTTP ошибка: {error}")
except requests.RequestException as error:
    print(f"Ошибка requests: {error}")
except psycopg.Error as error:
    print(f"Ошибка PostgreSQL: {error}")
except ValueError as error:
    print(f"Ошибка значения: {error}")
