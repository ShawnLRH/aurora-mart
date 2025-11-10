"""
AI utilities for Aurora-Mart personalization
- Decision Tree Classifier for cold-start category prediction
- Association Rules Mining for product recommendations
"""
import os
import pandas as pd
import joblib
from django.conf import settings


class CategoryPredictor:
    """Decision Tree Classifier for predicting preferred product category"""
    
    def __init__(self):
        model_path = os.path.join(settings.BASE_DIR, 'model', 'b2c_customers_100.joblib')
        self.model = joblib.load(model_path)
        
        # Define the feature columns used during training (extracted from actual model)
        # These are the columns after one-hot encoding
        self.feature_columns = [
            'age', 'household_size', 'has_children', 'monthly_income_sgd',
            'gender_Female', 'gender_Male',
            'employment_status_Full-time', 'employment_status_Part-time', 
            'employment_status_Retired', 'employment_status_Self-employed', 
            'employment_status_Student',
            'occupation_Admin', 'occupation_Education', 
            'occupation_Sales', 'occupation_Service', 
            'occupation_Skilled Trades', 'occupation_Tech',
            'education_Bachelor', 'education_Diploma', 
            'education_Doctorate', 'education_Master', 
            'education_Secondary'
        ]
        
        # Mapping from form values to model values
        self.occupation_mapping = {
            'Tech': 'Tech',
            'Sales': 'Sales',
            'Service': 'Service',
            'Admin': 'Admin',
            'Education': 'Education',
            'Skilled Trades': 'Skilled Trades',
            'Healthcare': 'Service',  # Map Healthcare to Service (closest match)
            'Other': 'Service'  # Map Other to Service as fallback
        }
        
        self.education_mapping = {
            'Secondary': 'Secondary',
            'Diploma': 'Diploma',
            'Bachelor': 'Bachelor',
            'Master': 'Master',
            'Doctorate': 'Doctorate'
        }
    
    def predict_category(self, customer_data):
        """
        Predict preferred category for a new customer
        
        Args:
            customer_data (dict): Dictionary with keys:
                - age (int)
                - household_size (int)
                - has_children (bool or int: 0/1)
                - monthly_income_sgd (float)
                - gender (str): 'Male' or 'Female'
                - employment_status (str): 'Full-time', 'Part-time', 'Self-employed', 'Student', 'Retired'
                - occupation (str): 'Tech', 'Sales', 'Service', 'Admin', 'Education', 'Skilled Trades'
                - education (str): 'Secondary', 'Diploma', 'Bachelor', 'Master', 'Doctorate'
        
        Returns:
            str: Predicted category (e.g., 'Electronics', 'Beauty & Personal Care', etc.)
        """
        # Map form values to model values
        mapped_data = customer_data.copy()
        mapped_data['occupation'] = self.occupation_mapping.get(
            customer_data['occupation'], 
            'Service'  # Default fallback
        )
        mapped_data['education'] = self.education_mapping.get(
            customer_data['education'], 
            'Diploma'  # Default fallback
        )
        
        # Convert raw input to DataFrame
        input_df = pd.DataFrame([mapped_data])
        
        # One-hot encode categorical variables
        input_encoded = pd.get_dummies(
            input_df, 
            columns=['gender', 'employment_status', 'occupation', 'education']
        )
        
        # Ensure all required columns are present, add missing columns as 0
        for col in self.feature_columns:
            if col not in input_encoded.columns:
                input_encoded[col] = 0
        
        # Reorder columns to match training data
        input_encoded = input_encoded[self.feature_columns]
        
        # Make prediction
        prediction = self.model.predict(input_encoded)
        return prediction[0]


class ProductRecommender:
    """Association Rules Mining for product recommendations"""
    
    def __init__(self):
        model_path = os.path.join(settings.BASE_DIR, 'model', 'b2c_products_500_transactions_50k.joblib')
        self.rules = joblib.load(model_path)
    
    def get_recommendations(self, items, metric='confidence', top_n=5):
        """
        Get product recommendations based on association rules
        
        Args:
            items (list): List of SKU codes (e.g., ['AIA-JM4T8BP6', 'GGB-FD0TVBDI'])
            metric (str): Metric to sort by ('confidence', 'lift', 'support')
            top_n (int): Number of recommendations to return
        
        Returns:
            list: List of recommended SKU codes
        """
        recommendations = set()
        
        for item in items:
            # Find rules where the item is in the antecedents
            matched_rules = self.rules[self.rules['antecedents'].apply(lambda x: item in x)]
            
            # Sort by the specified metric and get the top N
            top_rules = matched_rules.sort_values(by=metric, ascending=False).head(top_n)
            
            for _, row in top_rules.iterrows():
                recommendations.update(row['consequents'])
        
        # Remove items that are already in the input list
        recommendations.difference_update(items)
        
        return list(recommendations)[:top_n]
    
    def get_frequently_bought_together(self, sku, top_n=4):
        """
        Get products frequently bought together with the given SKU
        
        Args:
            sku (str): Product SKU code
            top_n (int): Number of recommendations to return
        
        Returns:
            list: List of recommended SKU codes with their metrics
        """
        # Find rules where the SKU is in the antecedents
        matched_rules = self.rules[self.rules['antecedents'].apply(lambda x: sku in x)]
        
        if matched_rules.empty:
            return []
        
        # Sort by lift (indicates strong association) and confidence
        top_rules = matched_rules.sort_values(
            by=['lift', 'confidence'], 
            ascending=False
        ).head(top_n)
        
        recommendations = []
        for _, row in top_rules.iterrows():
            for consequent in row['consequents']:
                if consequent != sku:
                    recommendations.append({
                        'sku': consequent,
                        'confidence': round(row['confidence'], 2),
                        'lift': round(row['lift'], 2)
                    })
        
        return recommendations[:top_n]
    
    def get_cart_recommendations(self, cart_items, top_n=3):
        """
        Get "Complete the Set" recommendations based on current cart
        
        Args:
            cart_items (list): List of SKU codes currently in cart
            top_n (int): Number of recommendations to return
        
        Returns:
            list: List of recommended SKU codes
        """
        if not cart_items:
            return []
        
        return self.get_recommendations(cart_items, metric='lift', top_n=top_n)


# Singleton instances for efficiency
_category_predictor = None
_product_recommender = None


def get_category_predictor():
    """Get or create CategoryPredictor instance"""
    global _category_predictor
    if _category_predictor is None:
        _category_predictor = CategoryPredictor()
    return _category_predictor


def get_product_recommender():
    """Get or create ProductRecommender instance"""
    global _product_recommender
    if _product_recommender is None:
        _product_recommender = ProductRecommender()
    return _product_recommender
