from flask import Blueprint, request, jsonify
from datetime import date
from .models import db, Deck, FlashCard
import random
import csv
import io

# Create a Flask Blueprint for the REST API
# All endpoints are mounted under /api
api = Blueprint('api', __name__, url_prefix='/api')


# ==================== DECK ROUTES ====================
# Routes for creating, reading, updating, and deleting decks.

@api.route('/decks', methods=['GET'])
def get_decks():
    """Get all decks"""
    decks = Deck.query.all()
    return jsonify([deck.to_dict() for deck in decks])


@api.route('/decks', methods=['POST'])
def create_deck():
    """Create a new deck"""
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'error': 'Deck name is required'}), 400
    
    if Deck.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Deck name already exists'}), 400
    
    deck = Deck(
        name=data['name'],
        description=data.get('description', '')
    )
    db.session.add(deck)
    db.session.commit()
    
    return jsonify(deck.to_dict()), 201


@api.route('/decks/<int:deck_id>', methods=['GET'])
def get_deck(deck_id):
    """Get deck details"""
    deck = Deck.query.get_or_404(deck_id)
    return jsonify(deck.to_dict())


@api.route('/decks/<int:deck_id>', methods=['PUT'])
def update_deck(deck_id):
    """Update a deck"""
    deck = Deck.query.get_or_404(deck_id)
    data = request.get_json()
    
    if 'name' in data:
        # Check if new name already exists
        existing = Deck.query.filter_by(name=data['name']).first()
        if existing and existing.id != deck_id:
            return jsonify({'error': 'Deck name already exists'}), 400
        deck.name = data['name']
    
    if 'description' in data:
        deck.description = data['description']
    
    db.session.commit()
    return jsonify(deck.to_dict())


@api.route('/decks/<int:deck_id>', methods=['DELETE'])
def delete_deck(deck_id):
    """Delete a deck"""
    deck = Deck.query.get_or_404(deck_id)
    db.session.delete(deck)
    db.session.commit()
    return '', 204


@api.route('/decks/<int:deck_id>/stats', methods=['GET'])
def get_deck_stats(deck_id):
    """Get deck statistics"""
    deck = Deck.query.get_or_404(deck_id)
    cards = deck.cards
    
    total = len(cards)
    due = len([c for c in cards if c.is_due()])
    learned = len([c for c in cards if c.reps >= 3])
    
    # Count by rating
    ratings = {}
    for card in cards:
        rating = card.get_rating()
        ratings[rating] = ratings.get(rating, 0) + 1
    
    # Count by status
    new = sum(1 for c in cards if c.reps == 0 and c.interval == 0)
    learning = sum(1 for c in cards if 0 < c.reps < 3)
    mastered = sum(1 for c in cards if c.reps >= 3)
    
    # Calculate mastery percentage
    if total > 0:
        mastery = (mastered * 3 + learning * 1.5) / (total * 3) * 100
    else:
        mastery = 0
    
    return jsonify({
        'total_cards': total,
        'cards_due': due,
        'cards_learned': learned,
        'mastery_percentage': round(mastery, 1),
        'ratings': ratings,
        'status_counts': {
            'new': new,
            'learning': learning,
            'mastered': mastered
        }
    })


# ==================== FLASHCARD ROUTES ====================
# Routes for working with individual flashcards and deck card lists.

@api.route('/decks/<int:deck_id>/cards', methods=['GET'])
def get_cards(deck_id):
    """Get all cards in a deck"""
    deck = Deck.query.get_or_404(deck_id)
    cards = deck.cards
    
    # Filter by due status if requested
    show_due_only = request.args.get('due_only', 'false').lower() == 'true'
    if show_due_only:
        cards = [c for c in cards if c.is_due()]
    
    return jsonify([card.to_dict() for card in cards])


@api.route('/decks/<int:deck_id>/cards', methods=['POST'])
def create_card(deck_id):
    """Create a new card in a deck"""
    deck = Deck.query.get_or_404(deck_id)
    data = request.get_json()
    
    if not data or not data.get('word') or not data.get('definition'):
        return jsonify({'error': 'Word and definition are required'}), 400
    
    card = FlashCard(
        deck_id=deck_id,
        word=data['word'],
        definition=data['definition']
    )
    db.session.add(card)
    db.session.commit()
    
    return jsonify(card.to_dict(show_definition=True)), 201


@api.route('/cards/<int:card_id>', methods=['GET'])
def get_card(card_id):
    """Get card details"""
    card = FlashCard.query.get_or_404(card_id)
    return jsonify(card.to_dict(show_definition=True))


@api.route('/cards/<int:card_id>', methods=['PUT'])
def update_card(card_id):
    """Update a card"""
    card = FlashCard.query.get_or_404(card_id)
    data = request.get_json()
    
    if 'word' in data:
        card.word = data['word']
    if 'definition' in data:
        card.definition = data['definition']
    
    db.session.commit()
    return jsonify(card.to_dict(show_definition=True))


@api.route('/cards/<int:card_id>', methods=['DELETE'])
def delete_card(card_id):
    """Delete a card"""
    card = FlashCard.query.get_or_404(card_id)
    db.session.delete(card)
    db.session.commit()
    return '', 204


@api.route('/cards/<int:card_id>/rate', methods=['POST'])
def rate_card(card_id):
    """
    Rate a card and update using SM-2 algorithm
    
    Quality values:
        0 = Unknown
        1 = Hard
        2 = Medium
        3 = Memorized
        5 = Perfectly Memorized
    """
    card = FlashCard.query.get_or_404(card_id)
    data = request.get_json()
    
    if 'quality' not in data:
        return jsonify({'error': 'Quality rating is required'}), 400
    
    quality = data['quality']
    if quality not in [0, 1, 2, 3, 5]:
        return jsonify({'error': 'Invalid quality value'}), 400
    
    card.update_sm2(quality)
    db.session.commit()
    
    return jsonify(card.to_dict(show_definition=True))


@api.route('/cards/<int:card_id>/reset', methods=['POST'])
def reset_card(card_id):
    """Reset a card to initial state"""
    card = FlashCard.query.get_or_404(card_id)
    card.reset()
    db.session.commit()
    return jsonify(card.to_dict(show_definition=True))


@api.route('/decks/<int:deck_id>/random-card', methods=['GET'])
def get_random_card(deck_id):
    """Return a single random card that is due for review."""
    deck = Deck.query.get_or_404(deck_id)
    due_cards = [c for c in deck.cards if c.is_due()]
    
    # If no card is due, respond with a clear payload indicating completion.
    if not due_cards:
        return jsonify({'card': None, 'message': 'No cards due for review'}), 200
    
    card = random.choice(due_cards)
    return jsonify({'card': card.to_dict(show_definition=True)})


@api.route('/decks/<int:deck_id>/bulk-reset', methods=['POST'])
def bulk_reset_cards(deck_id):
    """Reset all cards in a deck"""
    deck = Deck.query.get_or_404(deck_id)
    for card in deck.cards:
        card.reset()
    db.session.commit()
    return jsonify({'message': f'Reset {len(deck.cards)} cards'}), 200


# ==================== CSV IMPORT ====================
# Endpoint to import a deck from uploaded CSV content.

@api.route('/decks/import-csv', methods=['POST'])
def import_csv_file():
    """
    Import flashcards from a CSV file.
    
    Expected format:
    - Column 1: German word
    - Column 2: English definition
    - Optional header row
    
    Request body:
    {
        "deck_name": "Deck Name",
        "file_content": "base64 encoded CSV content"
    }
    """
    data = request.get_json()
    
    if not data or not data.get('deck_name') or not data.get('file_content'):
        return jsonify({'error': 'Deck name and file content are required'}), 400
    
    deck_name = data['deck_name'].strip()
    if not deck_name:
        return jsonify({'error': 'Deck name cannot be empty'}), 400
    
    # Check if deck already exists
    existing_deck = Deck.query.filter_by(name=deck_name).first()
    if existing_deck:
        return jsonify({'error': f'Deck "{deck_name}" already exists'}), 400
    
    try:
        # Decode file content
        import base64
        file_content = data['file_content']
        
        # Handle base64 encoded content
        if 'base64,' in file_content:
            file_content = file_content.split('base64,')[1]
        
        decoded_content = base64.b64decode(file_content).decode('utf-8')
        
        # Create new deck
        deck = Deck(
            name=deck_name,
            description=f"Imported from CSV file"
        )
        db.session.add(deck)
        db.session.commit()
        
        # Parse CSV
        csv_lines = decoded_content.strip().split('\n')
        imported_count = 0
        skipped_count = 0
        
        # Check if first row looks like headers
        first_row = csv_lines[0].lower()
        start_row = 0
        if 'word' in first_row or 'german' in first_row or 'definition' in first_row or 'english' in first_row:
            start_row = 1
        
        # Process each row
        reader = csv.reader(csv_lines[start_row:])
        for row_num, row in enumerate(reader, start=start_row + 1):
            if not row or len(row) < 2:
                skipped_count += 1
                continue
            
            word = row[0].strip()
            definition = row[1].strip()
            
            if word and definition:
                card = FlashCard(
                    deck_id=deck.id,
                    word=word,
                    definition=definition,
                    next_due=date.today()
                )
                db.session.add(card)
                imported_count += 1
            else:
                skipped_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'deck_id': deck.id,
            'deck_name': deck_name,
            'imported_cards': imported_count,
            'skipped_rows': skipped_count,
            'message': f'Imported {imported_count} cards into "{deck_name}"'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Import failed: {str(e)}'}), 400


# ==================== HEALTH CHECK ====================

@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok'}), 200
