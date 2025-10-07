import requests
import time
import hashlib
import json
from config import SHOPEE_APP_ID, SHOPEE_SECRET

def convert_shopee_links(links: list) -> list:
    """Conecta-se à API da Shopee para converter links, um por um."""
    converted_links = []
    for link in links:
        try:
            api_url = "https://open-api.affiliate.shopee.com.br/graphql"
            timestamp = int(time.time())
            graphql_query = f'mutation{{generateShortLink(input:{{originUrl:"{link}"}}){{shortLink}}}}'
            request_body = {"query": graphql_query}
            body_str = json.dumps(request_body)
            base_string = f"{str(SHOPEE_APP_ID)}{timestamp}{body_str}{SHOPEE_SECRET}"
            signature = hashlib.sha256(base_string.encode('utf-8')).hexdigest()
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"SHA256 Credential={SHOPEE_APP_ID}, Timestamp={timestamp}, Signature={signature}"
            }
            response = requests.post(api_url, data=body_str, headers=headers)
            response_data = response.json()
            if 'data' in response_data and response_data.get('data', {}).get('generateShortLink', {}).get('shortLink'):
                converted_links.append(response_data['data']['generateShortLink']['shortLink'])
            else:
                error_msg = response_data.get('errors', [{}])[0].get('message', 'Desconhecido')
                print(f"Erro da API Shopee ao converter {link[:30]}...: {error_msg}")
                converted_links.append(f"Erro ao converter o link.")
        except Exception as e:
            print(f"Exceção na conversão do link {link[:30]}...: {e}")
            converted_links.append(f"Erro técnico ao processar o link.")
    return converted_links

def resolve_short_link(url: str) -> str:
    """Segue os redirecionamentos para encontrar o URL final e completo de um link encurtado."""
    try:
        # Usamos um User-Agent de um browser comum para evitar bloqueios
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        # Usamos .head() para ser mais rápido, pois só queremos o URL final, não o conteúdo da página
        response = session.head(url, allow_redirects=True, timeout=10)
        final_url = response.url
        print(f"Link {url} resolvido para {final_url}")
        return final_url
    except requests.RequestException as e:
        print(f"Erro ao resolver o link {url}: {e}")
        return url # Em caso de erro, retorna o link original

