def process_data(products):
    for product in products:
        product['price'] = int(product['price'].replace(',', '')) if product['price'] != 'N/A' else 0
        product['review_count'] = int(product['review_count']) if product['review_count'].isdigit() else 0
        product['rating'] = float(product['rating']) if product['rating'] != 'N/A' else 0
    return products

def analyze_data(products):
    if not products:
        return {
            "평균 가격": 0,
            "최고 가격 상품": "N/A",
            "최저 가격 상품": "N/A",
            "평균 평점": 0,
            "총 리뷰 수": 0
        }

    total_price = sum(p['price'] for p in products)
    total_reviews = sum(p['review_count'] for p in products)
    valid_ratings = [p['rating'] for p in products if p['rating'] > 0]
    
    return {
        "평균 가격": total_price / len(products),
        "최고 가격 상품": max(products, key=lambda x: x['price'])['name'],
        "최저 가격 상품": min(products, key=lambda x: x['price'])['name'],
        "평균 평점": sum(valid_ratings) / len(valid_ratings) if valid_ratings else 0,
        "총 리뷰 수": total_reviews,
    }

def sort_products(products, sort_by):
    if sort_by == 'sales':
        return sorted(products, key=lambda x: x['review_count'], reverse=True)  # Use review count as a proxy for sales
    elif sort_by == 'review_count':
        return sorted(products, key=lambda x: x['review_count'], reverse=True)
    elif sort_by == 'rating':
        return sorted(products, key=lambda x: x['rating'], reverse=True)
    elif sort_by == 'price_high':
        return sorted(products, key=lambda x: x['price'], reverse=True)
    elif sort_by == 'price_low':
        return sorted(products, key=lambda x: x['price'])
    else:  # Default: no sorting (coupang_ranking)
        return products