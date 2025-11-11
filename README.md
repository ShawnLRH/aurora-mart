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
- 👤 User authentication with email verification (6-digit codes)
- 🛒 Shopping cart with real-time stock validation
- 📦 Product detail pages with ratings and stock information
- 💳 Complete checkout process with shipping addresses
- 📋 Order management and tracking system
- ✅ Order completion and refund functionality
- ⭐ Product reviews with verified purchase badges
- 📝 Customer review system (write reviews after delivery)
- 🗄️ SQLite database with sample data
- 📱 Responsive Bootstrap design (Pure CSS, no JavaScript)

### AI-Powered Personalization 🤖
- **Decision Tree Classification**: Predicts preferred product category based on demographic data during signup
- **Association Rules Mining**: Provides "Frequently Bought Together" recommendations
- **Smart Cart Suggestions**: "Complete the Set" recommendations based on cart contents
- **Personalized Home Page**: Featured products tailored to user's predicted preferences
- **Data-Driven**: Trained on 50,000 real transaction records

### Admin Panel 🔧
- **Product Management**: Create, edit, delete products with SKU validation
- **Inventory Control**: Stock adjustment, low stock alerts, out-of-stock tracking
- **CSV Operations**: Bulk import/export products with error handling
- **Customer Management**: View and edit customer profiles with AI category prediction
- **Order Management**: View, search, and manage all customer orders with status updates
- **Support Tickets**: Customer support system with email responses
- **Bulk Operations**: Bulk price updates by category
- **Staff Management**: Create and manage admin users
- **System Logs**: Complete audit trail of all admin actions with IP tracking
- **AI Analytics Dashboard**: View Decision Tree prediction insights with interactive pie chart showing category distribution
- **Product Bundling Recommendations**: View top 50 "Frequently Bought Together" product pairs with support, confidence, and lift metrics

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

5. **Create a superuser account** (for admin panel access)
```bash
python3 manage.py createsuperuser
```
Follow the prompts to set:
- Username: Enter `admin` (or press Enter to use your system username)
- Email address: Any valid email (e.g., admin@auroramart.com)
- Password: At least 8 characters with letters and numbers (ignore "too common" warning if testing locally, just type 'y')

After that, head to http://127.0.0.1:8000/adminpanel/ to access the dashboard for the admin panel.

**Note**: Admin panel credentials are separate from customer accounts. Only superusers can access http://127.0.0.1:8000/adminpanel/

6. **Load sample data** (100 customers, 500 products)
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

7. **Unzip model.zip into a model folder**

8. **Run the development server**
```bash
python3 manage.py runserver
```

9. **Access the application**

Open your browser and navigate to:
- **Main site**: http://127.0.0.1:8000
- **Load data**: http://127.0.0.1:8000/loaddata/ (import CSV data)
- **Admin Panel**: http://127.0.0.1:8000/adminpanel/ (use superuser credentials)

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
│   ├── models.py               # Database models (Customer, Product, Cart, SupportTicket)
│   ├── views.py                # View functions with AI integration
│   ├── urls.py                 # App URL routing
│   ├── forms.py                # Form definitions (signup, contact support)
│   ├── ai_utils.py             # AI model utilities
│   ├── context_processors.py  # Global template context
│   ├── templates/              # HTML templates
│   └── migrations/             # Database migrations
├── adminpanel/                 # Custom admin panel
│   ├── models.py               # SystemLog model
│   ├── views.py                # Admin views (products, customers, support, etc.)
│   ├── forms.py                # Admin forms
│   ├── urls.py                 # Admin URL routing
│   ├── templates/              # Admin panel templates
│   └── migrations/             # Admin panel migrations
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

### Order Models
- **Order**: Complete order tracking with multiple statuses (Received, Sent, Delivered, Completed, Refunded, Cancelled)
- **OrderItem**: Individual line items with SKU, name, quantity, and pricing
- **Address**: Shipping address storage with default address support
- Automatic stock reduction on purchase
- Automatic stock restoration on refund
- Order completion workflow (customer confirms delivery)
- Refund request system with reason tracking

### Review Model
- **Review**: Customer product reviews with 1-5 star ratings
- Verified purchase badges (only customers who bought the product can review)
- One review per product per order constraint
- Automatic product rating calculation based on review averages
- Review title and detailed comment support
- Timestamp tracking for created and updated reviews

### Support Ticket Model
- **SupportTicket**: Customer support requests with admin responses
- Status tracking (Open/Resolved)
- Email notifications and response history

### Admin Models
- **SystemLog**: Audit trail for all admin actions (CREATE, UPDATE, DELETE, IMPORT, EXPORT, BULK_UPDATE)

### AI Models
- **Decision Tree**: Trained on 100 customer profiles, predicts 1 of 10+ product categories
- **Association Rules**: Extracted from 50k transactions, confidence threshold 99%, min support 22%

## Usage

### Standard E-commerce Flow
1. **Browse Products**: Visit the home page to see featured and popular products
2. **Search & Filter**: Search by name or SKU with keyword highlighting, filter by category
3. **View Details**: Click on any product to see detailed information, AI recommendations, and customer reviews
4. **Sign Up**: Create an account with email verification (6-digit code sent to console)
5. **Add to Cart**: Add products to your shopping cart with real-time stock validation
6. **Checkout**: Complete purchase with shipping address and payment method selection
7. **Track Orders**: View order status progression (Received → Sent → Delivered)
8. **Complete Order**: After delivery, confirm receipt or request refund with automatic stock restoration
9. **Write Reviews**: Leave product reviews after receiving your order (verified purchase badge included)

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

#### 5. AI Insights Dashboard (Admin Panel)
Admins can view comprehensive AI analytics at `/adminpanel/ai/insights/`:
- **Category Predictions**: Interactive pie chart showing distribution of most often predicted customer categories
- **Prediction Statistics**: Table with counts and percentages per category showing which product categories the Decision Tree model predicts most frequently
- **Business Intelligence**: Understand which categories drive customer acquisition and help with inventory planning

#### 6. Product Bundling Recommendations (Admin Panel)
Actionable insights for business strategy at `/adminpanel/ai/rules/`:
- **Top 50 Product Pairs**: Most popular product combinations sorted by frequency
- **Support Metrics**: How often items are bought together (Support %)
- **Confidence Metrics**: Likelihood that customers who buy Product 1 also buy Product 2 (Confidence %)
- **Lift Metrics**: How much more likely the pair is bought together vs. randomly (Lift)
- **Business Applications**: Use these insights for product bundling, store layout optimization, and targeted marketing campaigns
- **High Quality Rules**: All recommendations are from 997K+ association rules with strict confidence thresholds (≥99%)

### Order Management Flow

#### Customer Workflow
1. **Place Order**: Complete checkout to create order (status: ORDER_RECEIVED)
2. **Track Progress**: View order status in "My Orders" section
3. **Receive Delivery**: Admin updates status to DELIVERED
4. **Confirm or Refund**: Two options appear after delivery:
   - ✅ **Received**: Mark order as COMPLETED (confirms satisfaction)
   - 💰 **Request Refund**: Submit refund reason, automatically restores stock and changes status to REFUNDED
5. **Write Reviews**: After delivery or completion, review products with "Write Review" button
   - Rate products 1-5 stars
   - Add review title and detailed comments
   - Verified purchase badge automatically added
   - View all reviews in "My Reviews" section

#### Admin Workflow
1. **View Orders**: Access Order Management from admin panel dashboard
2. **Search & Filter**: Find orders by Order ID, customer email, or status
3. **Update Status**: Change order status (Received → Sent → Delivered)
4. **Monitor Refunds**: Track refunded orders and automatic stock restoration
5. **Manage Reviews**: View and moderate customer reviews in admin panel

#### Order Statuses
- **ORDER_RECEIVED**: Initial status after checkout
- **ORDER_SENT**: Order shipped by admin
- **DELIVERED**: Order delivered to customer (reviews can be written)
- **COMPLETED**: Customer confirmed receipt (reviews can be written)
- **REFUNDED**: Customer requested refund, stock restored
- **CANCELLED**: Order cancelled (by admin or system)

### Review System

#### Writing Reviews
- **Eligibility**: Only customers who purchased the product can write reviews
- **Timing**: Reviews can be written after order status is DELIVERED or COMPLETED
- **Rating**: 1-5 star rating with visual selection
- **Content**: Title (max 200 chars) and detailed comment required
- **Verification**: All reviews automatically marked as "Verified Purchase"
- **Uniqueness**: One review per product per order (prevents duplicate reviews)

#### Viewing Reviews
- **Product Pages**: Reviews displayed in tabs with rating statistics
- **Rating Summary**: Visual breakdown of star ratings with percentages
- **My Reviews**: Personal dashboard showing all reviews you've written
- **Pagination**: Reviews paginated (5 per page on product pages, 10 on My Reviews)

#### Review Features
- Automatic product rating calculation (average of all reviews)
- Visual star displays (⭐) for ratings
- Review timestamps (creation and update dates)
- Verified purchase badges on all reviews
- Quick access via user profile dropdown

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
- **Bootstrap 5.3.3**: Responsive UI framework (CSS only, no JavaScript)
- **Bootstrap Icons**: Icon library
- **Pure CSS**: All interactions (dropdowns, tabs, forms) implemented without JavaScript
- **Django Templates**: Server-side rendering with template inheritance

### Database & Data
- **SQLite3**: Embedded database
- **CSV Import**: Bulk data loading (100 customers, 500 products, 50k transactions)

## License

This project is created for educational purposes.
