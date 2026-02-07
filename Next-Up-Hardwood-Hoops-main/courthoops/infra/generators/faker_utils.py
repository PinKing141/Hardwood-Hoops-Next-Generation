from faker import Faker

faker = Faker()


def random_player_name() -> str:
    return faker.name()


def random_school_name(level: str = "HS") -> str:
    city = faker.city()
    if level.upper() == "AAU":
        return f"{city} Elite"
    if level.upper() == "HS":
        return f"{city} High"
    return f"{city} {faker.color_name()}s"
