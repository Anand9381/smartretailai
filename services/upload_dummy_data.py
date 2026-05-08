from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from dotenv import load_dotenv
import os

load_dotenv()

# ==============================
# AZURE AI SEARCH CONFIG
# ==============================

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX")
API_KEY = os.getenv("AZURE_SEARCH_KEY")

client = SearchClient(
    endpoint=SEARCH_ENDPOINT,
    index_name=INDEX_NAME,
    credential=AzureKeyCredential(API_KEY)
)

# ==============================
# SMART RETAIL KNOWLEDGE BASE
# ==============================

documents = [

    # =========================================
    # RETURN POLICY
    # =========================================

    {
        "id": "policy_return_1",
        "title": "Return and Refund Policy",
        "content": """
Customers can return products within 7 days of delivery.

Products must be unused, undamaged, and returned with original packaging.

Refunds are usually processed within 5 business days after successful inspection.

Electronics products may require additional verification before refund approval.

Repeated high-frequency returns from the same account may trigger manual review.

Exchange requests are supported for eligible products depending on stock availability.

Products damaged during delivery can be replaced immediately after verification.
        """,
        "category": "policy"
    },

    # =========================================
    # SHIPPING POLICY
    # =========================================

    {
        "id": "policy_shipping_1",
        "title": "Shipping and Delivery Policy",
        "content": """
Orders are usually processed within 1 to 2 business days.

Standard delivery takes approximately 3 to 7 business days depending on the destination.

Customers receive shipment tracking updates after dispatch.

Express delivery may be available for selected cities and products.

Large sale events and holidays may slightly increase delivery timelines.

Orders with multiple products may arrive in separate shipments.

Failed delivery attempts may require customer confirmation before re-dispatch.
        """,
        "category": "shipping"
    },

    # =========================================
    # WARRANTY RULES
    # =========================================

    {
        "id": "policy_warranty_1",
        "title": "Warranty and Product Protection",
        "content": """
Most electronics products include 1 year manufacturer warranty.

Warranty covers manufacturing defects only.

Physical damage, liquid damage, and unauthorized repairs are not covered.

Customers may contact support for warranty claim assistance.

Smart devices and accessories may have separate warranty durations.

Replacement approval depends on manufacturer verification.
        """,
        "category": "warranty"
    },

    # =========================================
    # INVENTORY RULES
    # =========================================

    {
        "id": "inventory_rules_1",
        "title": "Inventory and Stock Management Rules",
        "content": """
Products with stock below 20 units are considered low stock.

Fast-selling products should be prioritized for restocking.

High-demand products may experience temporary stock shortages during sales events.

Inventory levels are monitored continuously to reduce stock-out situations.

Products with consistently low sales may be moved to promotional campaigns.

Electronics and premium accessories typically experience higher inventory fluctuations.
        """,
        "category": "inventory"
    },

    # =========================================
    # TRENDING PRODUCTS
    # =========================================

    {
        "id": "analytics_trending_1",
        "title": "Trending Products Analytics",
        "content": """
Wireless Headphones Pro, Smart Watch Ultra, and Gaming Laptop X15 are currently trending products.

Electronics category has shown consistently high demand over recent weeks.

Products with strong customer reviews and repeat purchases are considered trending.

Smart watches and wireless accessories have shown significant growth in customer engagement.

Seasonal promotions and discounts strongly influence trending products.
        """,
        "category": "analytics"
    },

    # =========================================
    # SALES ANALYTICS
    # =========================================

    {
        "id": "analytics_sales_1",
        "title": "Sales Performance Insights",
        "content": """
Electronics category contributes the highest revenue across the platform.

Weekend sales are usually higher than weekday sales.

Wireless accessories, gaming products, and smart devices show strong repeat purchases.

Customers often purchase accessories along with premium electronics.

Higher discounts generally improve order conversion rates.

Flash sales and festive offers significantly increase platform traffic and sales.
        """,
        "category": "analytics"
    },

    # =========================================
    # LOW STOCK ANALYTICS
    # =========================================

    {
        "id": "analytics_low_stock_1",
        "title": "Low Stock and Demand Insights",
        "content": """
Smart Watch Ultra and Gaming Laptop X15 frequently experience low stock because of strong customer demand.

Wireless audio products sell faster during discount campaigns.

Products with increasing wishlist activity often become low stock quickly.

Restocking delays may occur because of supplier limitations.

High-demand products should be prioritized for warehouse replenishment.
        """,
        "category": "analytics"
    },

    # =========================================
    # CUSTOMER SHOPPING BEHAVIOR
    # =========================================

    {
        "id": "customer_behavior_1",
        "title": "Customer Shopping Behavior",
        "content": """
Customers usually purchase electronics during weekends and festive sales.

Younger customers prefer wireless accessories and gaming products.

Customers often compare products before placing high-value orders.

Products with better ratings and reviews generally receive more orders.

Discounts and free shipping significantly improve customer conversions.

Premium customers frequently purchase smart devices and accessories together.
        """,
        "category": "customer"
    },

    # =========================================
    # PRICING RULES
    # =========================================

    {
        "id": "pricing_rules_1",
        "title": "Pricing and Discount Insights",
        "content": """
Electronics products usually receive higher discounts during festive campaigns.

Gaming products experience strong demand even with smaller discounts.

Dynamic pricing may increase prices temporarily during high demand periods.

Products with low stock and high demand may experience slight price increases.

Bundle offers improve sales for accessories and wearable products.
        """,
        "category": "pricing"
    },

    # =========================================
    # RECOMMENDATION RULES
    # =========================================

    {
        "id": "recommendation_rules_1",
        "title": "Recommendation and Personalization Rules",
        "content": """
Customers searching for gaming products are often recommended gaming accessories.

Wireless audio buyers are frequently interested in smart watches and fitness bands.

Products with similar categories, ratings, and customer interests are recommended together.

Returning customers usually receive personalized recommendations based on previous orders.

Popular products with strong reviews are prioritized in recommendation results.
        """,
        "category": "recommendation"
    },

    # =========================================
    # ANOMALY DETECTION
    # =========================================

    {
        "id": "ml_anomaly_1",
        "title": "Sales Anomaly Detection Rules",
        "content": """
Unexpected spikes in orders may indicate viral product popularity or promotional success.

Sudden drops in sales may indicate inventory shortages, pricing issues, or reduced demand.

Repeated failed payments may indicate suspicious activity.

Abnormal order volume from a single region may require operational verification.

Large overnight sales spikes are automatically reviewed by the analytics system.
        """,
        "category": "ml"
    },

    # =========================================
    # FORECASTING RULES
    # =========================================

    {
        "id": "ml_forecast_1",
        "title": "Demand Forecasting Insights",
        "content": """
Electronics demand is expected to increase during festive seasons and major sales campaigns.

Gaming products and smart accessories show strong long-term growth potential.

Forecasting models use historical sales, stock movement, and customer demand trends.

Products with rising search frequency often experience future sales growth.

Demand forecasting helps reduce inventory shortages and improve warehouse planning.
        """,
        "category": "ml"
    },

    # =========================================
    # CUSTOMER SUPPORT FAQ
    # =========================================

    {
        "id": "faq_support_1",
        "title": "Customer Support FAQ",
        "content": """
Customers can track orders from the Orders page after login.

Support is available through email, live chat, and phone assistance.

Payment failures may occur because of banking issues or network interruptions.

Customers can cancel eligible orders before shipment confirmation.

Order status updates are sent through email and notifications.

Account verification may be required for high-value purchases.
        """,
        "category": "faq"
    }

]

# ==============================
# UPLOAD DOCUMENTS
# ==============================

result = client.upload_documents(documents)

print("Smart Retail AI knowledge uploaded successfully!")