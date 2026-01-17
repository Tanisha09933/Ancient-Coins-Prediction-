from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import or_, inspect
from . import scraper, db
from .models import (
    AncientDynastyKey, AncientCoinData,
    MedievalDynastyKey, MedievalCoinData,
    ModernDynastyKey, ModernCoinData
)
from .image_finder import find_image_path

# --- AI Model Integration ---
from ai_model.predictor import Predictor

predictor = None
try:
    predictor = Predictor()
except RuntimeError as e:
    print(f"!!!!!!!!!!\nFATAL AI MODEL ERROR during initial load: {e}\n!!!!!!!!!!")

bp = Blueprint('main', __name__)

MODEL_MAP = {
    'ancient': {'keys': AncientDynastyKey, 'data': AncientCoinData},
    'medieval': {'keys': MedievalDynastyKey, 'data': MedievalCoinData},
    'modern': {'keys': ModernDynastyKey, 'data': ModernCoinData}
}


def table_exists(table_name):
    inspector = inspect(db.engine)
    return inspector.has_table(table_name)


@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/api/ai-identify', methods=['POST'])
def ai_identify():
    """
    Receives an uploaded image, classifies it using the AI, and searches the web.
    Database search is skipped as per request.
    """
    global predictor
    if predictor is None:
        print("[AI Identify] Error: Predictor object was not loaded successfully.")
        return jsonify({"error": "AI model is not available. Check server logs."}), 503

    if 'coin_image' not in request.files:
        return jsonify({"error": "No image file provided."}), 400

    image_file = request.files['coin_image']
    image_bytes = image_file.read()
    if not image_bytes:
        return jsonify({"error": "Image file is empty."}), 400

    print("[AI Identify] Received image. Getting prediction...")
    ai_prediction = predictor.predict(image_bytes)

    if "error" in ai_prediction:
        return jsonify({"error": ai_prediction['error']}), 400

    predicted_class = ai_prediction.get('predicted_class')
    print(f"[AI Identify] Model prediction: '{predicted_class}'. Skipping database search.")

    try:
        # --- WEB SCRAPER LOGIC ---
        # Use the AI's prediction to search the web
        scraper_query = f"{predicted_class} coin numismatics"
        print(f"[Web] Running scraper with AI prediction: '{scraper_query}'")
        web_results = scraper.multi_search_snippets(query=scraper_query, max_results=3)

        return jsonify({
            'ai_prediction': ai_prediction,
            'database_results': [],  # Empty list as requested
            'web_results': web_results
        })

    except Exception as e:
        print(f"[AI Identify] Error: {e}")
        return jsonify({
            'ai_prediction': ai_prediction,
            'database_results': [],
            'web_results': [],
            'error': "An error occurred during web search."
        }), 500


@bp.route('/api/search')
def api_search():
    """The main API endpoint that performs text-based searches across all periods."""
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify({"error": "A query parameter is required."}), 400

    print(f"\n[Backend] Received search query: '{query}'")

    try:
        db_results = []
        search_terms = query.split()

        for period, models in MODEL_MAP.items():
            KeyModel, DataModel = models['keys'], models['data']
            if not table_exists(KeyModel.__tablename__) or not table_exists(DataModel.__tablename__):
                continue

            print(f"[Database] Searching in '{period}' tables...")
            dynasty_query_filters = [
                or_(KeyModel.dynasty.like(f'%{term}%'), KeyModel.king_name.like(f'%{term}%'))
                for term in search_terms
            ]
            matched_keys = KeyModel.query.filter(or_(*dynasty_query_filters)).all()

            if matched_keys:
                for key in matched_keys:
                    coins = DataModel.query.filter(DataModel.code.startswith(key.code)).all()
                    for coin in coins:
                        coin_dict = coin.to_dict_with_key_info(key)
                        coin_dict['image_url'] = find_image_path(coin_dict)
                        db_results.append(coin_dict)
            else:
                print(f"[Database] No matching keys found in '{period}' tables for this query.")

        scraper_query = f"{query} coin numismatics"
        web_results = scraper.multi_search_snippets(query=scraper_query, max_results=3)

        return jsonify({
            'database_results': db_results,
            'web_results': web_results
        })

    except Exception as e:
        db.session.rollback()
        print(f"[Backend] An error occurred: {e}")
        return jsonify({"error": "Sorry, something went wrong on our end."}), 500