"""
CSV Import Script
This script helps you import flashcards from a CSV file into the web app database.

CSV Format (required):
    word,definition
    German word,English translation
    ...

Usage:
    1. Place your CSV file in the same directory as this script
    2. Run: python import_csv.py your_deck_name your_file.csv
    3. The deck will be created and cards imported
"""

import sys
import csv
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from app import create_app
from app.models import db, Deck, FlashCard


def import_csv(deck_name: str, csv_file: str) -> None:
    """Import flashcards from a CSV file"""
    
    # Check if file exists
    if not Path(csv_file).exists():
        print(f"❌ Error: File '{csv_file}' not found")
        return
    
    # Create app context
    app = create_app()
    
    with app.app_context():
        # Check if deck already exists
        existing_deck = Deck.query.filter_by(name=deck_name).first()
        if existing_deck:
            print(f"⚠️  Deck '{deck_name}' already exists")
            response = input("Overwrite? (yes/no): ").lower()
            if response != 'yes':
                print("❌ Import cancelled")
                return
            # Delete existing deck
            db.session.delete(existing_deck)
            db.session.commit()
        
        # Create new deck
        deck = Deck(name=deck_name, description=f"Imported from {csv_file}")
        db.session.add(deck)
        db.session.commit()
        print(f"✅ Created deck: {deck_name}")
        
        # Read CSV and import cards
        imported_count = 0
        errors = 0
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # If no headers, try positional
                if reader.fieldnames is None or 'word' not in reader.fieldnames:
                    f.seek(0)
                    reader = csv.reader(f)
                    for row_num, row in enumerate(reader, 1):
                        if len(row) >= 2:
                            word = row[0].strip()
                            definition = row[1].strip()
                            
                            if word and definition:
                                card = FlashCard(
                                    deck_id=deck.id,
                                    word=word,
                                    definition=definition
                                )
                                db.session.add(card)
                                imported_count += 1
                        else:
                            errors += 1
                else:
                    # With headers
                    for row in reader:
                        word = row.get('word', '').strip()
                        definition = row.get('definition', '').strip()
                        
                        if word and definition:
                            card = FlashCard(
                                deck_id=deck.id,
                                word=word,
                                definition=definition,
                                next_due=date.today(),
                                next_due=date.today()
                            )
                            db.session.add(card)
                            imported_count += 1
                        else:
                            errors += 1
            
            db.session.commit()
            print(f"\n✅ Import complete!")
            print(f"   • Cards imported: {imported_count}")
            if errors > 0:
                print(f"   • Errors/skipped: {errors}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error during import: {e}")


def main():
    """Main entry point"""
    if len(sys.argv) < 3:
        print("Usage: python import_csv.py <deck_name> <csv_file>")
        print("\nExample: python import_csv.py 'German Verbs' verbs.csv")
        print("\nCSV Format:")
        print("  word,definition")
        print("  Laufen,To run")
        print("  Gehen,To go")
        sys.exit(1)
    
    deck_name = sys.argv[1]
    csv_file = sys.argv[2]
    
    print(f"Importing from {csv_file}...")
    print(f"Deck name: {deck_name}\n")
    
    import_csv(deck_name, csv_file)


if __name__ == '__main__':
    main()
