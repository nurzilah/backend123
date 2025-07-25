from flask import Blueprint, jsonify
import requests
from bs4 import BeautifulSoup
from app.model.article import Article
from datetime import datetime

scrape_bp = Blueprint('scrape_bp', __name__)  # ✅ Pakai nama unik

@scrape_bp.route('/scrape_bells_palsy', methods=['POST'])
def scrape_bells_palsy():
    url = 'https://www.gooddoctor.co.id/hidup-sehat/penyakit/penyakit-bells-palsy-menyerang-siapapun/'

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        return jsonify({'error': f'Failed to fetch page: {e}'}), 500

    soup = BeautifulSoup(response.text, 'html.parser')
    headers = soup.find_all('h2', class_='wp-block-heading')
    if not headers:
        return jsonify({'error': 'No <h2> with class wp-block-heading found'}), 404

    hasil = []

    for header in headers:
        title = header.text.strip()
        definisi_parts = []
        image_url = None

        sibling = header.find_next_sibling()
        while sibling and sibling.name != 'h2':
            if sibling.name == 'p':
                definisi_parts.append(sibling.text.strip())
            elif sibling.name in ['figure', 'div', 'section']:
                img_tag = sibling.find('img')
                if img_tag and img_tag.has_attr('src'):
                    src = img_tag['src']
                    if src.startswith('http') and not image_url:
                        image_url = src
            sibling = sibling.find_next_sibling()

        if not image_url:
            first_img = soup.find('img', src=True)
            if first_img:
                src = first_img['src']
                if src.startswith('http'):
                    image_url = src

        definisi = "\n\n".join(definisi_parts)

        article = Article(
            title=title,
            definisi=definisi,
            image=image_url,
            url=url,
            timestamp=datetime.utcnow()
        )

        try:
            article.save()
        except Exception as e:
            print(f"[ERROR] Gagal menyimpan artikel '{title}': {e}")
            continue

        hasil.append({
            'title': title,
            'definisi': definisi,
            'image': image_url
        })

    return jsonify({'message': f'{len(hasil)} artikel berhasil disimpan!', 'data': hasil}), 201

@scrape_bp.route('/bells_palsy_articles', methods=['GET'])
def get_articles():
    articles = Article.objects().order_by('-timestamp')
    return jsonify([{
        'id': str(a.id),
        'title': a.title,
        'definisi': a.definisi[:100] + "...",
        'full_definisi': a.definisi
    } for a in articles]), 200
