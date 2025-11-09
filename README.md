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

- 🛍️ Product catalog with categories and search
- 👤 User authentication (login, signup, logout)
- 🛒 Product detail pages with ratings
- 📊 Customer and product data management
- 💾 SQLite database with sample data
- 📱 Responsive design

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
pip install django
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
├── aurora/              # Main project settings
│   ├── settings.py     # Django configuration
│   ├── urls.py         # Main URL routing
│   └── wsgi.py         # WSGI configuration
├── ecommerce/          # Main application
│   ├── models.py       # Database models (Customer, Product)
│   ├── views.py        # View functions
│   ├── urls.py         # App URL routing
│   ├── forms.py        # Form definitions
│   ├── templates/      # HTML templates
│   └── migrations/     # Database migrations
├── data/               # CSV data files
│   ├── b2c_customers_100.csv
│   └── b2c_products_500.csv
├── static/             # Static files (CSS, JS, images)
├── db.sqlite3          # SQLite database
└── manage.py           # Django management script
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

## Usage

1. **Browse Products**: Visit the home page to see featured and popular products
2. **View Details**: Click on any product to see detailed information
3. **Sign Up**: Create an account to access personalized features
4. **Login**: Access your account with credentials

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

- **Backend**: Python 3.x, Django 5.x
- **Database**: SQLite3
- **Frontend**: HTML, CSS, JavaScript
- **Data**: CSV files for bulk import

## License

This project is created for educational purposes.
