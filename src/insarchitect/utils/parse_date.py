import sys

def parse_date_from_int(date: int) -> str:
    date = str(date)
    if len(date) != 8:
        print(f"Unvalid date: {date}, must be: YYYYMMDD")
        sys.exit(1)

    year = date[0:4]
    month = date[4:6]
    day = date[6:8]

    if int(month) > 12:
        print(f"Unvalid month value: {month}")
        sys.exit(1)
    if int(day) > 31:
        print(f"Unvalid day value: {day}")
        sys.exit(1)

    return f"{year}-{month}-{day}"
