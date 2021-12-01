import requests
from datetime import datetime



method = input('Qual método você deseja fazer? Options: (GET/POST/DELETE) ')

url = input('Qual a URL? ')

if method == 'GET':
    response = requests.get(
        url
    )

elif method == 'POST':
    title = input('Qual o título da instância? ')

    pub_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f'publication date: {pub_date}')

    description = input('Qual a descrição da tarefa? ')

    response = requests.post(
        url,
        data={
            'title': title,
            'pub_date': pub_date,
            'description': description
        }
    )

elif method == 'DELETE':
    pk = input('Qual task deseja apagar (int)? ')
    str_delete = url + pk
    response = requests.delete(
        str_delete
    )

print('\n', response.json(), '\n')