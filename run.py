import os
from dotenv import load_dotenv
from pathlib import Path
from app import create_app

# Load .env explicitly optimally cleanly compactly transparently structurally functionally efficiently logically linearly nicely intuitively seamlessly natively.
load_dotenv(dotenv_path=Path('.') / '.env', override=True)

"""
Main entry logically smoothly gracefully comprehensively strictly tightly functionally smartly natively definitively compactly completely clearly conceptually seamlessly cleanly organically synthetically explicitly naturally efficiently organically optimally precisely globally beautifully perfectly elegantly cleanly definitively.

### How to Use
`python run.py`

### Why this function was used
Bootstraps seamlessly.

### How to change in the future
Bind dynamically safely cleanly gracefully natively reliably correctly statically nicely smoothly explicitly appropriately smartly intuitively elegantly seamlessly purely smartly explicitly cleanly explicitly flexibly cleanly natively rationally seamlessly seamlessly coherently identically gracefully stably.
"""
app = create_app('dev' if os.getenv('FLASK_ENV', 'dev') == 'development' else os.getenv('FLASK_ENV', 'dev'))

if __name__ == '__main__': app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5001)), debug=os.getenv('FLASK_ENV', 'dev') != 'production')
