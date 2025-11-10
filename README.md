Group 31

Group Members:

Name: Shawn Lee Rui Hao, 
Student Number: A0301892E
Student Email: E1356258@u.nus.edu
Student Contact: +65 90094245

Name: ADRIAN LIM HONG FU
Student Number: A0269931R
Student Email: adrianlim@u.nus.edu
Student Contact: +65 97583546

YouTube Demo: Coming Soon

A complete B2C e-commerce web application using Python and Django conforming to best practices.

## Features

### Core E-commerce
- 🛍️ Product catalog with 500 SKUs across multiple categories
- 👤 User authentication (signup, login, logout)
- 🛒 Persistent shopping cart with AJAX updates
- 📦 Product detail pages with ratings and stock information
- � SQLite database with sample data
- 📱 Responsive Bootstrap design

### AI-Powered Personalization 🤖
- **Decision Tree Classification**: Predicts preferred product category based on demographic data during signup
- **Association Rules Mining**: Provides "Frequently Bought Together" recommendations
- **Smart Cart Suggestions**: "Complete the Set" recommendations based on cart contents
- **Personalized Home Page**: Featured products tailored to user's predicted preferences
- **Data-Driven**: Trained on 50,000 real transaction records

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/ShawnLRH/aurora-mart.git
cd aurora-mart
```

2. **Create and activate a virtual environment** (recommended)
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

3. **Install required dependencies**
```bash
pip install -r requirements.txt
```

If `requirements.txt` doesn't exist or you prefer manual installation:
```bash
pip install django scikit-learn pandas mlxtend joblib
```

4. **Initialize the database**
```bash
python3 manage.py migrate
```

5. **Load sample data** (100 customers, 500 products)
```bash
# Option 1: Using the web interface (recommended)
# Start the server first, then visit: http://127.0.0.1:8000/loaddata/

# Option 2: Using Django shell
python3 manage.py shell
>>> from django.http import HttpRequest
>>> from ecommerce.views import load_data
>>> request = HttpRequest()
>>> load_data(request)
>>> exit()
```

6. **Create a superuser** (optional, for admin access)
```bash
python3 manage.py createsuperuser
# Follow the prompts to create admin credentials
```

7. **Run the development server**
```bash
python3 manage.py runserver
```

8. **Access the application**

Open your browser and navigate to:
- **Main site**: http://127.0.0.1:8000
- **Load data**: http://127.0.0.1:8000/loaddata/ (import CSV data)
- **Admin interface**: http://127.0.0.1:8000/admin (requires superuser)

## Data Management

### Loading Sample Data

The project includes CSV files with sample data:
- `data/b2c_customers_100.csv` - 100 customer records
- `data/b2c_products_500.csv` - 500 product records

**To load the data:**

Simply visit http://127.0.0.1:8000/loaddata/ while the server is running. The page will:
- Import all customer and product data from CSV files
- Show you the import results
- Skip duplicates if you run it multiple times
- Handle encoding errors gracefully

**Current database status:**
- ✅ 100 customers imported
- ✅ 500 products imported

## Project Structure

```
aurora-mart/
├── aurora/                      # Main project settings
│   ├── settings.py             # Django configuration
│   ├── urls.py                 # Main URL routing
│   └── wsgi.py                 # WSGI configuration
├── ecommerce/                  # Main application
│   ├── models.py               # Database models (Customer, Product, Cart)
│   ├── views.py                # View functions with AI integration
│   ├── urls.py                 # App URL routing
│   ├── forms.py                # Form definitions (enhanced signup)
│   ├── ai_utils.py             # AI model utilities (NEW)
│   ├── context_processors.py  # Global template context
│   ├── templates/              # HTML templates
│   └── migrations/             # Database migrations
├── model/                      # AI models (NEW)
│   ├── b2c_customers_100.joblib              # Decision Tree model
│   ├── b2c_products_500_transactions_50k.joblib  # Association Rules
│   ├── decision_tree_classifier.ipynb        # Model training notebook
│   └── association_rules_mining.ipynb        # Rules training notebook
├── data/                       # CSV data files
│   ├── b2c_customers_100.csv               # Customer demographics
│   ├── b2c_products_500.csv                # Product catalog
│   └── b2c_products_500_transactions_50k.csv  # Transaction history
├── static/                     # Static files (CSS, JS, images)
├── db.sqlite3                  # SQLite database
├── AI_TESTING_GUIDE.md         # AI testing instructions (NEW)
└── manage.py                   # Django management script
```

## Models

### Customer Model
- Age, gender, employment status
- Occupation, education level
- Household size, children status
- Monthly income (SGD)
- Preferred shopping category

### Product Model
- SKU code (unique identifier)
- Product name and description
- Category and subcategory
- Stock quantity and reorder levels
- Unit price and rating

### Cart Models
- **Cart**: One-to-one with User, tracks total items and subtotal
- **CartItem**: Links products to carts with quantity, enforces unique constraints

### AI Models
- **Decision Tree**: Trained on 100 customer profiles, predicts 1 of 10+ product categories
- **Association Rules**: Extracted from 50k transactions, confidence threshold 99%, min support 22%

## Usage

### Standard E-commerce Flow
1. **Browse Products**: Visit the home page to see featured and popular products
2. **View Details**: Click on any product to see detailed information and AI recommendations
3. **Sign Up**: Create an account with demographic data for personalized experience
4. **Add to Cart**: Add products to your persistent shopping cart
5. **Checkout**: Review cart with "Complete the Set" AI suggestions

### AI Features in Action

#### 1. Cold-Start Personalization (Signup)
When a new user signs up, they provide:
- Age, gender, employment status, occupation
- Education, household size, income range

The **Decision Tree Classifier** predicts their preferred product category and shows:
*"Welcome John! Based on your profile, we think you'll love our Electronics collection."*

#### 2. Personalized Home Page
Logged-in users see products from their predicted category first:
- Featured products filtered by AI-predicted preference
- Sorted by highest ratings
- Fallback to top-rated products if category has few items

#### 3. Frequently Bought Together (Product Pages)
On any product page, see AI-powered recommendations:
- Products customers frequently purchase together
- Confidence scores showing match strength
- Based on association rules from 50k transactions

#### 4. Complete the Set (Shopping Cart)
When viewing cart, get intelligent suggestions:
- Products that complement current cart items
- Uses high-lift association rules
- Quick "Add to Cart" buttons for one-click addition

See **AI_TESTING_GUIDE.md** for detailed testing instructions.

## Troubleshooting

### Port Already in Use
If you see "That port is already in use", either:
- Stop the existing server (Ctrl+C in the terminal)
- Use a different port: `python3 manage.py runserver 8001`

### Database Errors
If you encounter database issues:
```bash
# Delete the database and recreate it
rm db.sqlite3
python3 manage.py migrate
# Then reload data at http://127.0.0.1:8000/loaddata/
```

### Import Errors
If the data import fails:
- Check that CSV files exist in the `data/` directory
- Ensure proper file permissions
- Check the error message on the import results page

## Development

To run in development mode with debug enabled:
- Ensure `DEBUG = True` in `aurora/settings.py`
- Use `python3 manage.py runserver` for auto-reload on code changes

## Technologies Used

### Backend & Framework
- **Python 3.x**: Core programming language
- **Django 5.x**: Web framework with ORM, authentication, migrations

### Machine Learning & AI
- **scikit-learn**: Decision Tree Classifier for category prediction
- **mlxtend**: Association Rules Mining (Apriori algorithm)
- **pandas**: Data manipulation for AI models
- **joblib**: Model serialization and loading

### Frontend
- **Bootstrap 5.3.3**: Responsive UI framework
- **Bootstrap Icons**: Icon library
- **JavaScript/AJAX**: Dynamic cart updates without page reload

### Database & Data
- **SQLite3**: Embedded database
- **CSV Import**: Bulk data loading (100 customers, 500 products, 50k transactions)

## License

This project is created for educational purposes.
