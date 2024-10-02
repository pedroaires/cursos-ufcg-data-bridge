import requests
from requests.exceptions import HTTPError


class APIClient:
    def __init__(self, auth_url, base_url, username, password, need_token=False) -> None:
        self.auth_url = auth_url
        self.base_url = base_url
        self.username = username
        self.password = password
        self.token =  self.get_token() if need_token else None
        self.headers = {
            'accept': 'application/json',
            'Authentication-Token': self.token
        } if need_token else {
            'accept': 'application/json'
        }
    
    def get_token(self):
        body = {
            "credentials": {
                "username": self.username,
                "password": self.password
            }
        }
        try:
            print(f"Requisitando token de autenticação em {self.auth_url}")
            response = requests.post(self.auth_url, json=body)
            response.raise_for_status()
            return response.json()['token']
        except HTTPError as http_err:
            print(f"Ocorreu um erro HTTP durante requisição de criação do token: {http_err}")
        except Exception as err:
            print(f"Algum erro ocorreu durante requisição de criação do token: {err}")

    def request(self, endpoint, method="GET", params=None, data=None, json_data=None):
        full_url = f"{self.base_url}{endpoint}"
        try:
            if method.upper() == "GET":
                response = requests.get(full_url, headers=self.headers, params=params)
            elif method.upper() == "POST":
                response = requests.post(full_url, headers=self.headers, params=params, data=data, json=json_data)
            elif method.upper() == "PUT":
                response = requests.put(full_url, headers=self.headers, params=params, data=data, json=json_data)
            elif method.upper() == "DELETE":
                response = requests.delete(full_url, headers=self.headers, params=params)
            else:
                raise ValueError("Método HTTP não suportado")
            
            return response
        except HTTPError as http_err:
            print(f"Ocorreu um erro HTTP durante a requisição: {http_err}")
        except Exception as err:
            print(f"Algum erro ocorreu durante a requisição: {err}")