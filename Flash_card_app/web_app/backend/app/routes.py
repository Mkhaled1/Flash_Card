import base64
import binascii
import csv
import io
import random
from datetime import date

from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from .models import db, Deck, FlashCard

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


@api.route('/decks/merge', methods=['POST'])
def merge_decks():
    """Create a new deck containing copies of cards from selected decks."""
    data = request.get_json(silent=True) or {}
    name = data.get('name', '').strip() if isinstance(data.get('name'), str) else ''
    raw_deck_ids = data.get('deck_ids')

    if not name:
        return jsonify({'error': 'A name for the merged deck is required'}), 400
    if not isinstance(raw_deck_ids, list) or any(
        isinstance(deck_id, bool) or not isinstance(deck_id, int) or deck_id <= 0
        for deck_id in raw_deck_ids
    ):
        return jsonify({'error': 'Select at least two valid decks'}), 400

    deck_ids = list(dict.fromkeys(raw_deck_ids))
    if len(deck_ids) < 2:
        return jsonify({'error': 'Select at least two different decks'}), 400
    if Deck.query.filter_by(name=name).first():
        return jsonify({'error': 'Deck name already exists'}), 400

    source_decks = Deck.query.filter(Deck.id.in_(deck_ids)).all()
    if len(source_decks) != len(deck_ids):
        return jsonify({'error': 'One or more selected decks no longer exist'}), 404

    source_by_id = {deck.id: deck for deck in source_decks}
    ordered_sources = [source_by_id[deck_id] for deck_id in deck_ids]
    source_cards = [card for deck in ordered_sources for card in deck.cards]
    if not source_cards:
        return jsonify({'error': 'The selected decks contain no cards'}), 400

    merged_deck = Deck(
        name=name,
        description=data.get(
            'description',
            'Merged from: ' + ', '.join(deck.name for deck in ordered_sources),
        ),
    )
    db.session.add(merged_deck)
    db.session.flush()

    for card in source_cards:
        db.session.add(FlashCard(
            deck_id=merged_deck.id,
            word=card.word,
            definition=card.definition,
            reps=card.reps,
            interval=card.interval,
            ef=card.ef,
            next_due=card.next_due,
        ))

    db.session.commit()
    return jsonify(merged_deck.to_dict()), 201


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
    
    return jsonify([card.to_dict(show_definition=True) for card in cards])


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
    """Return the next weighted study card, prioritizing due cards."""
    deck = Deck.query.get_or_404(deck_id)
    include_all = request.args.get('include_all', 'false').lower() == 'true'
    exclude_id = request.args.get('exclude_id', type=int)
    study_cards = [
        card for card in deck.cards
        if card.get_rating() != 'Perfectly Memorized'
    ]

    if include_all and deck.cards and not study_cards:
        return jsonify({'card': None, 'message': 'All cards are mastered'}), 200
    if include_all and not deck.cards:
        return jsonify({'card': None, 'message': 'This deck has no cards yet'}), 200

    due_cards = [card for card in study_cards if card.is_due()]
    candidates = due_cards or (study_cards if include_all else [])
    if not candidates:
        return jsonify({'card': None, 'message': 'No cards due for review'}), 200

    if exclude_id is not None and len(candidates) > 1:
        other_cards = [card for card in candidates if card.id != exclude_id]
        if other_cards:
            candidates = other_cards

    weights = {
        'New': 5.0,
        'Unknown': 4.0,
        'Hard': 3.0,
        'Medium': 2.0,
        'Memorized': 1.0,
        'Perfectly Memorized': 0.5,
    }
    card = random.choices(
        candidates,
        weights=[weights.get(item.get_rating(), 1.0) for item in candidates],
        k=1,
    )[0]
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
    data = request.get_json(silent=True)
    
    if not isinstance(data, dict) or not data.get('deck_name') or not data.get('file_content'):
        return jsonify({'error': 'Deck name and file content are required'}), 400
    
    deck_name = data['deck_name'].strip() if isinstance(data['deck_name'], str) else ''
    if not deck_name:
        return jsonify({'error': 'Deck name cannot be empty'}), 400
    if not isinstance(data['file_content'], str):
        return jsonify({'error': 'CSV file content must be text'}), 400
    
    # Check if deck already exists
    existing_deck = Deck.query.filter_by(name=deck_name).first()
    if existing_deck:
        return jsonify({'error': f'Deck "{deck_name}" already exists'}), 400
    
    try:
        file_content = data['file_content']
        
        # Handle base64 encoded content
        if file_content.startswith('data:') and ',' in file_content:
            file_content = file_content.split(',', 1)[1]

        decoded_content = base64.b64decode(file_content, validate=True).decode('utf-8-sig')
    except (binascii.Error, UnicodeDecodeError, ValueError):
        return jsonify({'error': 'The uploaded file is not valid UTF-8 base64 CSV'}), 400

    rows = list(csv.reader(io.StringIO(decoded_content, newline='')))
    if not rows:
        return jsonify({'error': 'The CSV file is empty'}), 400

    # Accept both the basic two-column format and the desktop app's six-column format.
    header = [cell.strip().casefold() for cell in rows[0]]
    has_header = any(
        column in {'word', 'german', 'definition', 'english'}
        for column in header
    )
    if has_header:
        aliases = {
            'word': {'word', 'german'},
            'definition': {'definition', 'english'},
            'reps': {'reps', 'repetitions'},
            'interval': {'interval'},
            'ef': {'ef', 'ease_factor', 'ease factor'},
            'next_due': {'next_due', 'next_due_date', 'next review'},
        }
        columns = {
            key: next((index for index, value in enumerate(header) if value in names), None)
            for key, names in aliases.items()
        }
        data_rows = rows[1:]
    else:
        columns = {
            'word': 0,
            'definition': 1,
            'reps': 2,
            'interval': 3,
            'ef': 4,
            'next_due': 5,
        }
        data_rows = rows

    skipped_count = 0

    cards = []

    def value_for(row, column):
        index = columns[column]
        return row[index].strip() if index is not None and index < len(row) else ''

    for row in data_rows:
        if not row:
            skipped_count += 1
            continue

        word = value_for(row, 'word')
        definition = value_for(row, 'definition')
        if not word or not definition:
            skipped_count += 1
            continue

        try:
            reps = max(0, int(value_for(row, 'reps') or 0))
        except ValueError:
            reps = 0
        try:
            interval = max(0, int(value_for(row, 'interval') or 0))
        except ValueError:
            interval = 0
        try:
            ef = max(1.3, float(value_for(row, 'ef') or 2.5))
        except ValueError:
            ef = 2.5
        try:
            next_due_text = value_for(row, 'next_due')
            next_due = date.fromisoformat(next_due_text) if next_due_text else date.today()
        except ValueError:
            next_due = date.today()

        cards.append(FlashCard(
            word=word,
            definition=definition,
            reps=reps,
            interval=interval,
            ef=ef,
            next_due=next_due,
        ))

    if not cards:
        return jsonify({'error': 'The CSV contains no valid flashcards'}), 400

    deck = Deck(name=deck_name, description='Imported from CSV file')
    db.session.add(deck)
    db.session.flush()
    for card in cards:
        card.deck_id = deck.id
        db.session.add(card)

    db.session.commit()

    return jsonify({
        'success': True,
        'deck_id': deck.id,
        'deck_name': deck_name,
        'imported_cards': len(cards),
        'skipped_rows': skipped_count,
        'message': f'Imported {len(cards)} cards into "{deck_name}"'
    }), 201


@api.route('/decks/<int:deck_id>/export.csv', methods=['GET'])
def export_deck(deck_id):
    """Download a deck as a CSV that preserves its study progress."""
    deck = Deck.query.get_or_404(deck_id)
    output = io.StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow(['word', 'definition', 'reps', 'interval', 'ef', 'next_due'])
    for card in deck.cards:
        writer.writerow([
            card.word,
            card.definition,
            card.reps,
            card.interval,
            f'{card.ef:.3f}',
            card.next_due.isoformat(),
        ])

    filename = secure_filename(deck.name) or 'flashcards'
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'{filename}.csv',
    )


# ==================== HEALTH CHECK ====================

@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok'}), 200
