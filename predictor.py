##Börja testa ML här 
from database.queryTool import fetch_and_return_data


if __name__ == "__main__":
    data_result = fetch_and_return_data("1998-05", "60s")

    print("hej")