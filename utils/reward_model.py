import json
import requests


def get_reward_score_from_rm_ziya(prompt: str, response: str) -> float:
    url = 'a_secret_url_to_make_a_request'
    headers = {'Content-Type': 'application/json', 'token': '20548cb5a329260ead027437cb22590e945504abd419e2e44ba312feda2ff29e'}
    payload = json.dumps({"query": prompt, "response": response})
    response = requests.request("POST", url, headers=headers, data=payload)
    eva_score = float(eval(response.text)["res"])
    return eva_score

if __name__ == '__main__':
    h = get_reward_score_from_rm_ziya('test', 'test')
    print(h)